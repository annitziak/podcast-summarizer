from pathlib import Path
import tempfile, requests, json
import os
import imageio_ffmpeg as ffmpeg
import whisperx, torch

# --------------------------------------------------------------------
# FFmpeg fix: force WhisperX to use the imageio-ffmpeg binary
# --------------------------------------------------------------------
ffmpeg_path = ffmpeg.get_ffmpeg_exe()
print("Using ffmpeg at:", ffmpeg_path)

# Export and patch so WhisperX always finds the binary
os.environ["FFMPEG_BINARY"] = ffmpeg_path
os.environ["PATH"] = os.path.dirname(ffmpeg_path) + os.pathsep + os.environ["PATH"]

import whisperx.audio
whisperx.audio.FFMPEG_BINARY = ffmpeg_path
# --------------------------------------------------------------------


def download_file(url: str, out_path: Path):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(1024 * 256):
                if chunk:
                    f.write(chunk)
    return out_path


def transcribe_with_whisperx(audio_url: str, model_name: str = "small"):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "float32"

    model = whisperx.load_model(model_name, device, compute_type=compute_type)

    with tempfile.TemporaryDirectory() as td:
        local_audio = Path(td) / "episode.mp3"
        download_file(audio_url, local_audio)
        result = model.transcribe(str(local_audio))

    return {
        "language": result.get("language"),
        "text": result.get("text", "").strip(),
        "segments": result.get("segments", [])
    }

