import streamlit as st
import threading
from audio_engine import AudioEngine # type: ignore
from text_processor import TextProcessor
from streamlit.runtime.scriptrunner import add_script_run_ctx

st.set_page_config(layout="wide", page_title="Solaris", page_icon="⚡")

if "state" not in st.session_state:
    st.session_state.state = {
        "is_listening": False,
        "raw_text": "Ready. Check terminal after starting.",
        "clean_text": "",
        "logs": []
    }
    with st.spinner("Initializing Engines..."):
        st.session_state.processor = TextProcessor()
        st.session_state.audio = AudioEngine()

# --- CALLBACKS ---
def on_partial(text):
    st.session_state.state["raw_text"] = text
    st.rerun()

def on_final(text):
    st.session_state.state["raw_text"] = "..." 
    mode = st.session_state.get("mode", "Neutral")
    cleaned, stats = st.session_state.processor.process(text, mode)
    st.session_state.state["clean_text"] += f" {cleaned}"
    log = f"⏱️ **{stats['total_ms']:.0f} ms** | Input: *{text}*"
    st.session_state.state["logs"].insert(0, log)
    st.rerun()

# --- CONTROL ---
def start_mic():
    if st.session_state.state["is_listening"]: return
    st.session_state.state["is_listening"] = True
    st.session_state.state["raw_text"] = "🎧 Calibrating... (See Terminal)"
    
    thread = threading.Thread(
        target=st.session_state.audio.listen_loop, 
        args=(on_final, on_partial), 
        daemon=True
    )
    add_script_run_ctx(thread)
    thread.start()

def stop_mic():
    st.session_state.audio.stop()
    st.session_state.state["is_listening"] = False
    st.session_state.state["raw_text"] = "🔴 Stopped."
    st.rerun()

# --- UI ---
st.title("⚡ Solaris Dictation")

col_ctl, col_mode, col_stat = st.columns([1, 2, 1])
with col_ctl:
    if not st.session_state.state["is_listening"]:
        st.button("🎙️ START", type="primary", on_click=start_mic, use_container_width=True)
    else:
        st.button("🛑 STOP", type="secondary", on_click=stop_mic, use_container_width=True)

with col_mode:
    st.selectbox("Style", ["Neutral", "Formal", "Casual", "Concise"], key="mode", label_visibility="collapsed")

with col_stat:
    st.markdown("🟢 Live" if st.session_state.state["is_listening"] else "🔴 Offline")

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.subheader("🗣️ Raw Streaming")
    st.info(st.session_state.state["raw_text"])
with col2:
    st.subheader("✨ Final Output")
    st.success(st.session_state.state["clean_text"])

if st.session_state.state["logs"]:
    st.caption("Metrics:")
    for log in st.session_state.state["logs"][:3]:
        st.markdown(f"- {log}")