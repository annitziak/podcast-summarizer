import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"  # your FastAPI backend

st.set_page_config(page_title="Podcast Summarizer", page_icon="🎧", layout="centered")

st.title("🎧 Podcast Summarizer")
st.write("Turn podcast audio into transcripts and summaries with a single click.")

# --- Store selected episode ID in session ---
if "current_episode" not in st.session_state:
    st.session_state.current_episode = None

# Tabs for workflow
tab1, tab2, tab3 = st.tabs(["➕ Add Episode", "📝 Transcribe", "📑 Summarize"])

# --- Tab 1: Add Episode ---
with tab1:
    st.subheader("Add a New Podcast Episode")
    title = st.text_input("Episode Title")
    audio_url = st.text_input("Audio URL (MP3 or Spotify link)")

    if st.button("Add Episode", use_container_width=True):
        if not title or not audio_url:
            st.warning("Please provide both a title and audio URL.")
        else:
            resp = requests.post(f"{API_URL}/episodes/", params={"title": title, "audio_url": audio_url})
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.current_episode = data["id"]
                st.success(f"✅ Episode added (ID: {data['id']}, Status: {data['status']})")
            else:
                st.error(f"❌ Error: {resp.text}")

# --- Tab 2: Transcribe ---
with tab2:
    st.subheader("Generate Transcript with WhisperX")
    ep_id = st.number_input("Episode ID", min_value=1, step=1, value=st.session_state.current_episode or 1)

    if st.button("Transcribe Episode", use_container_width=True):
        resp = requests.post(f"{API_URL}/transcripts/{ep_id}")
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.current_episode = ep_id
            st.success("📝 Transcript generated!")
            with st.expander("Transcript Preview"):
                st.text_area("Transcript", data.get("preview", ""), height=200)
        else:
            st.error(f"❌ Error: {resp.text}")

# --- Tab 3: Summarize ---
# --- Tab 3: Summarize ---
with tab3:
    st.subheader("Summarize Transcript")
    ep_id = st.number_input("Episode ID to Summarize", min_value=1, step=1, value=st.session_state.current_episode or 1)

    if st.button("Summarize Episode", use_container_width=True):
        with st.spinner("✨ Summarizing transcript with LLM..."):
            resp = requests.post(f"{API_URL}/summaries/{ep_id}")
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.current_episode = ep_id
            st.success("📑 Summary generated!")

            # --- Show summary ---
            st.text_area("Episode Summary", data.get("summary", ""), height=200)

            # --- Show chapters ---
            if "chapters" in data and data["chapters"]:
                st.subheader("📂 Chapters")
                for chap in data["chapters"]:
                    # assuming each chap is {"timestamp": "MM:SS", "title": "something"}
                    ts = chap.get("timestamp", "??:??")
                    title = chap.get("title", "")
                    st.markdown(f"- **{ts}** → {title}")

            # --- Show quotes ---
            if "quotes" in data and data["quotes"]:
                st.subheader("💬 Key Quotes")
                for q in data["quotes"]:
                    st.markdown(f"> {q}")

        else:
            st.error(f"❌ Error: {resp.text}")
