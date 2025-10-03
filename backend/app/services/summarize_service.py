# services/summarize_service.py
import json
import openai
from textwrap import dedent
from dotenv import load_dotenv
import os

# ---------------- CONFIG ----------------
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-4o-mini"
CHUNK_SIZE = 1500   # adjust as needed
# ----------------------------------------

def chunk_segments(segments, max_chars=6000):
    """Split transcript into chunks without breaking segments."""
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
    """Send one chunk to the LLM and get JSON result"""
    prompt = dedent(f"""
    You are a podcast summarizer. Analyze the following transcript excerpt:

    ---
    {text}
    ---

    Return JSON with these keys:
    - "summary": 3–5 concise bullet points
    - "quotes": a list of short, memorable, or funny quotes
    - "chapters": a list of proposed chapters, each with:
        - "title": a short descriptive title
        - "timestamp": the starting time in MM:SS format
    """).strip()

    resp = openai.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(resp.choices[0].message.content)

def summarize_segments(segments):
    """Full pipeline: chunk → summarize → merge"""
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

    return final_summary
