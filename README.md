## 🎙️ Podcast Summarizer

A tool to fetch podcast episodes (from RSS or direct MP3), transcribe them with WhisperX, and prepare transcripts for summarization.

### ✨ Features
Uses RSS feed URLs
Resolves metadata (title, show, description, duration)
Downloads and validates audio (MP3, M4A, etc.)

### 📝 Transcription

WhisperX automatic speech recognition (ASR)
Accurate timestamped segments

### 📚 Summarization

Chunk long transcripts into manageable pieces
Summarize per chunk and merge into a full summary

Extract:

✅ Key takeaways
✅ Chapter breakdowns (with timestamps)
✅ Optional topics and sentiment

### 🎬 Highlights

Smart clip generation (30–60s) by scoring transcript segments (energy + novelty)
Export audiograms or short shareable highlights

### 💾 Storage

PostgreSQL schema with tables for:


### 🌐 Frontend

Streamlit app for users to:

Submit podcast URLs

Track processing status

View transcript, summary, and highlights

### ⚡ Backend

FastAPI for ingestion and coordination

Worker pipeline:

Ingest → Transcribe → Summarize → Highlight

Queue-based processing (scalable, async)