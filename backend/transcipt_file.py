"""
Usage:
  python transcribe_or_use_transcript.py meta.json --out out.json
  # Force using WhisperX even if a transcript_url exists:
  python transcribe_or_use_transcript.py meta.json --out out.json --force-whisper
  python transcipt_file.py example_entry.json --out episode_transcript.json
"""

from __future__ import annotations
import argparse
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests
from tqdm import tqdm

# --------------------------------------------------------------------
# FFmpeg fix: force WhisperX to use the imageio-ffmpeg binary
# --------------------------------------------------------------------
import imageio_ffmpeg as ffmpegio
ffmpeg_path = ffmpegio.get_ffmpeg_exe()
print("Using ffmpeg at:", ffmpeg_path)

# Add folder to PATH and export as FFMPEG_BINARY
os.environ["FFMPEG_BINARY"] = ffmpeg_path
os.environ["PATH"] = os.path.dirname(ffmpeg_path) + os.pathsep + os.environ["PATH"]

# Monkeypatch WhisperX to always use this binary
import whisperx.audio
whisperx.audio.FFMPEG_BINARY = ffmpeg_path

# -----------------------
# Helpers: transcript parsing
# -----------------------

def _parse_plain_text(text: str) -> Tuple[str, List[Dict[str, Any]]]:
    return text.strip(), []

_SRT_TIME = re.compile(r"(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2}),(?P<ms>\d{3})")
_VTT_TIME = re.compile(r"(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2})\.(?P<ms>\d{3})")

def _hms_to_seconds(match: re.Match) -> float:
    h = int(match.group("h")); m = int(match.group("m")); s = int(match.group("s")); ms = int(match.group("ms"))
    return h*3600 + m*60 + s + ms/1000.0

def _parse_srt(srt_text: str) -> Tuple[str, List[Dict[str, Any]]]:
    segments, block = [], []
    for line in srt_text.splitlines():
        line = line.strip("\ufeff").strip()
        if not line:
            if block:
                segments.extend(_parse_srt_block(block))
                block = []
        else:
            block.append(line)
    if block:
        segments.extend(_parse_srt_block(block))
    full_text = " ".join(seg["text"] for seg in segments).strip()
    return full_text, segments

def _parse_srt_block(lines: List[str]) -> List[Dict[str, Any]]:
    if len(lines) < 2:
        return []
    if lines[0].isdigit():
        lines = lines[1:]
    time_line = lines[0]
    m = re.findall(_SRT_TIME, time_line)
    if len(m) >= 2:
        start = _hms_to_seconds(_SRT_TIME.search(time_line))
        end = _hms_to_seconds(list(_SRT_TIME.finditer(time_line))[-1])
    else:
        return []
    text = " ".join(lines[1:]).strip()
    return [{"start": start, "end": end, "text": text}]

def _parse_vtt(vtt_text: str) -> Tuple[str, List[Dict[str, Any]]]:
    lines = [ln.strip("\ufeff") for ln in vtt_text.splitlines() if not ln.strip().startswith("NOTE")]
    content = "\n".join(lines)
    cues = re.split(r"\n\s*\n", content)
    segments = []
    for cue in cues:
        cue_lines = [l for l in cue.splitlines() if l.strip()]
        if not cue_lines or cue_lines[0].upper().startswith("WEBVTT"):
            continue
        time_idx = next((i for i, l in enumerate(cue_lines[:3]) if "-->" in l), None)
        if time_idx is None:
            continue
        times = [m for m in _VTT_TIME.finditer(cue_lines[time_idx])]
        if len(times) < 2:
            continue
        start = _hms_to_seconds(times[0]); end = _hms_to_seconds(times[1])
        text = " ".join(cue_lines[time_idx+1:]).strip()
        if text:
            segments.append({"start": start, "end": end, "text": text})
    full_text = " ".join(seg["text"] for seg in segments).strip()
    return full_text, segments

def _parse_json_transcript(js: Any) -> Tuple[str, List[Dict[str, Any]]]:
    if isinstance(js, dict):
        segments = js.get("segments", [])
        if isinstance(segments, list) and segments and isinstance(segments[0], dict):
            full_text = js.get("text") or " ".join(s.get("text","") for s in segments)
            norm = [{"start": float(s.get("start",0)), "end": float(s.get("end",0)),
                     "text": (s.get("text") or "").strip(),
                     **({"speaker": s.get("speaker")} if "speaker" in s else {})}
                    for s in segments]
            return full_text.strip(), norm
        if "text" in js and isinstance(js["text"], str):
            return js["text"].strip(), []
    elif isinstance(js, list) and js and isinstance(js[0], dict):
        norm = [{"start": float(s.get("start",0)), "end": float(s.get("end",0)),
                 "text": (s.get("text") or "").strip(),
                 **({"speaker": s.get("speaker")} if "speaker" in s else {})}
                for s in js]
        full_text = " ".join(s["text"] for s in norm).strip()
        return full_text, norm
    return _parse_plain_text(json.dumps(js, ensure_ascii=False))

def fetch_and_parse_transcript(transcript_url: str) -> Tuple[str, List[Dict[str, Any]]]:
    with requests.get(transcript_url, stream=True, timeout=60) as r:
        r.raise_for_status()
        ctype = (r.headers.get("content-type") or "").lower()
        data = r.content
    if "json" in ctype or transcript_url.lower().endswith(".json"):
        return _parse_json_transcript(json.loads(data.decode("utf-8", errors="ignore")))
    if "vtt" in ctype or transcript_url.lower().endswith(".vtt"):
        return _parse_vtt(data.decode("utf-8", errors="ignore"))
    if "srt" in ctype or transcript_url.lower().endswith(".srt"):
        return _parse_srt(data.decode("utf-8", errors="ignore"))
    return _parse_plain_text(data.decode("utf-8", errors="ignore"))

# -----------------------
# Helpers: download audio
# -----------------------

def download_file(url: str, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=None) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length") or 0)
        with open(out_path, "wb") as f, tqdm(total=total, unit="B", unit_scale=True, desc="Downloading"):
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)
    return out_path

# -----------------------
# WhisperX (CPU)
# -----------------------

# other options for model_name to try that are faster: tiny, base
def transcribe_with_whisperx(audio_path: Path, model_name: str = "small") -> Dict[str, Any]:
    import torch, whisperx
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "float32"

    print(f"[WhisperX] Loading ASR model={model_name} on {device} ({compute_type})")
    model = whisperx.load_model(model_name, device, compute_type=compute_type)

    print("[WhisperX] Transcribing...")
    result = model.transcribe(str(audio_path), language=None)
    language = result.get("language")
    segments = result.get("segments", [])
    full_text = (result.get("text") or "").strip()

    print("[WhisperX] Loading alignment model...")
    model_a, metadata = whisperx.load_align_model(language_code=language, device=device)
    aligned = whisperx.align(segments, model_a, metadata, str(audio_path), device)
    segments = aligned.get("segments", segments)

    norm_segments = [{"start": float(s.get("start",0)), "end": float(s.get("end",0)), "text": (s.get("text") or "").strip()} for s in segments]

    return {"language": language, "text": full_text, "segments": norm_segments}

# -----------------------
# Main
# -----------------------

def main():
    p = argparse.ArgumentParser(description="Use existing transcript if provided, else WhisperX (CPU) to transcribe audio.")
    p.add_argument("meta_json", type=str, help="Path to JSON metadata with at least audio_url, optionally transcript_url")
    p.add_argument("--out", type=str, required=True, help="Output JSON path for the unified transcript")
    p.add_argument("--force-whisper", action="store_true", help="Ignore transcript_url even if present; transcribe with WhisperX")
    p.add_argument("--model", type=str, default="small", help="WhisperX model (tiny|base|small|medium|large-v2). CPU users: small/medium recommended.")
    args = p.parse_args()

    meta = json.loads(Path(args.meta_json).read_text(encoding="utf-8"))
    if "audio_url" not in meta and "input" in meta and isinstance(meta["input"], dict):
        meta = meta["input"]

    audio_url = meta.get("mp3_url") or meta.get("audio_url")
    transcript_url = meta.get("transcript_url")

    if not audio_url and not transcript_url:
        raise SystemExit("meta_json must contain at least 'audio_url' or 'transcript_url'.")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if transcript_url and not args.force_whisper:
        print(f"[Info] Using provided transcript_url: {transcript_url}")
        full_text, segments = fetch_and_parse_transcript(transcript_url)
        result = {"language": None, "text": full_text, "segments": segments}
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[Done] Saved transcript → {out_path}")
        return

    if not audio_url:
        raise SystemExit("No 'audio_url' available to transcribe with WhisperX.")

    with tempfile.TemporaryDirectory() as td:
        name = os.path.basename(audio_url.split("?")[0]) or "episode.mp3"
        local_audio = Path(td) / name
        print(f"[Download] {audio_url}")
        download_file(audio_url, local_audio)
        result = transcribe_with_whisperx(local_audio, model_name=args.model)

    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Done] Saved transcript → {out_path}")

if __name__ == "__main__":
    main()
