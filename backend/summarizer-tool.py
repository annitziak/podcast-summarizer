import json
import openai
from textwrap import dedent

# ---------------- CONFIG ----------------
MODEL_NAME = "gpt-4o-mini"   # or "gpt-4o", "gpt-4.1", etc.
CHUNK_SIZE = 1500            # approx tokens; adjust as needed
INPUT_FILE = "episode_transcript.json" #now for testing
OUTPUT_FILE = "episode_summary.json"

import os
from dotenv import load_dotenv

# load variables from .env
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY") # Set your OpenAI API key in the .env file
print("API Key loaded?", bool(openai.api_key))

print("Using model:", MODEL_NAME)
# ----------------------------------------


def load_transcript(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["segments"]


def chunk_segments(segments, max_chars=6000):
    """Split transcript into chunks without breaking segments. This is to ensure that we don't exceed the model's token limit."""
    chunks, current, length = [], [], 0
    for seg in segments:
        seg_text = seg["text"].strip()
        if length + len(seg_text) > max_chars and current:
            chunks.append(current)
            current, length = [], 0
        current.append(seg)
        length += len(seg_text)
    if current:
        chunks.append(current)
    return chunks


def summarize_chunk(text, start_time, end_time):
    """Send one chunk to the LLM"""
    prompt = dedent(f"""
    You are a podcast summarizer. Analyze the following transcript excerpt:

    ---
    {text}
    ---

    Return JSON with these keys:
    - "summary": 3–5 concise bullet points that capture the key ideas and events
    - "quotes": a list of short, memorable, or funny quotes
    - "chapters": a list of proposed chapters for this excerpt.
       Each chapter must have:
       - "title": a short descriptive title
       - "timestamp": the starting time in MM:SS format (approximate from the transcript)
    """).strip()

    resp = openai.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    print(f"Processed chunk {start_time} - {end_time}")

    return json.loads(resp.choices[0].message.content)


def process_transcript():
    segments = load_transcript(INPUT_FILE)
    chunks = chunk_segments(segments)

    all_results = []
    for chunk in chunks:
        text = " ".join(s["text"] for s in chunk)
        start_time, end_time = chunk[0]["start"], chunk[-1]["end"]
        result = summarize_chunk(text, start_time, end_time)
        all_results.append(result)

    final_summary = {
        "episode_summary": [pt for r in all_results for pt in r["summary"]],
        "key_quotes": [q for r in all_results for q in r["quotes"]],
        "chapters": [ch for r in all_results for ch in r.get("chapters", [])]
    }


    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_summary, f, indent=2)

    print(f"✅ Saved summary to {OUTPUT_FILE}")


if __name__ == "__main__":
    process_transcript()
