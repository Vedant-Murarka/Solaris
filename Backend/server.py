import numpy as np
import time
import scipy.signal
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from faster_whisper import WhisperModel # type: ignore
from text_processor import TextProcessor

app = FastAPI()

# --- 1. LOAD MODELS (OFFLINE) ---
print("⚡ Loading Whisper Model (Local)...")
model_path = "./models/whisper"
try:
    model = WhisperModel(model_path, device="cpu", compute_type="int8")
except Exception as e:
    print(f"❌ ERROR Loading Whisper: {e}")
    print("   -> Did you run 'python setup_models.py'?")
    raise

print("⚡ Loading Processor...")
processor = TextProcessor()
print("✅ Server Ready. Waiting for Extension...")

# --- 2. SERVE UI (For debugging, though we use Extension now) ---
@app.get("/")
async def get():
    # Assuming Frontend/interface.html or index.html is the current name/path
    with open("../Frontend/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# --- 3. HELPER FUNCTIONS ---
def resample_audio(audio_chunk_list, input_rate):
    """Resamples browser audio (e.g., 48k) to Whisper's required 16k."""
    if not audio_chunk_list: return np.array([], dtype=np.float32)
    
    audio_data = np.concatenate(audio_chunk_list)
    target_rate = 16000
    
    num_samples = int(len(audio_data) * float(target_rate) / input_rate)
    resampled_data = scipy.signal.resample(audio_data, num_samples)
    return resampled_data

async def process_buffer(audio_buffer, input_rate, processor, mode, t_start_override=None):
    """Transcribes and Cleans a chunk of audio."""
    if len(audio_buffer) < 5: return None 
    
    # 1. Start Timing (Use override time if provided, otherwise use current time)
    t_start = t_start_override if t_start_override is not None else time.time()
    
    # 2. Resample
    final_audio = resample_audio(audio_buffer, input_rate)
    
    # 3. Transcribe
    segments, _ = model.transcribe(
        final_audio, 
        beam_size=1, 
        initial_prompt="Umm, uh, like, you know, okay.", 
        condition_on_previous_text=False
    )
    raw_text = " ".join([s.text for s in segments]).strip()
    
    if len(raw_text) > 1:
        # 4. Clean & Tone
        final_text, stats = processor.process(raw_text, mode)
        total_latency = (time.time() - t_start) * 1000 # Calculate total time spent
        
        return {
            "type": "result", "raw": raw_text, "clean": final_text,
            "latency": f"{total_latency:.0f}", "breakdown": f"Clean:{stats['cleaning_ms']:.0f} | Gram:{stats['grammar_ms']:.0f}"
        }
    return None

# --- 4. WEBSOCKET HANDLER ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    mode = websocket.query_params.get("mode", "Neutral")
    client_rate = float(websocket.query_params.get("rate", 44100))
        
    print(f"\n🔌 Connected | Mode: {mode} | Input Rate: {client_rate}Hz")
    
    audio_buffer = [] 
    silence_chunks = 0
    
    # TUNING: Threshold 0.005 is very sensitive (from debugging)
    AMPLITUDE_THRESHOLD = 0.005 
    SILENCE_LIMIT = 15

    try:
        while True:
            message = await websocket.receive()

            if "bytes" in message:
                # --- AUDIO DATA ---
                data = message["bytes"]
                chunk_np = np.frombuffer(data, dtype=np.float32)
                
                volume = np.sqrt(np.mean(chunk_np**2))
                
                # --- REMOVED DEBUG PRINT HERE ---
                
                if volume > AMPLITUDE_THRESHOLD:
                    silence_chunks = 0
                    audio_buffer.append(chunk_np)
                else:
                    if len(audio_buffer) > 0:
                        silence_chunks += 1
                        audio_buffer.append(chunk_np) 
                    
                    # Silence Trigger (Auto-process)
                    if silence_chunks > SILENCE_LIMIT and len(audio_buffer) > 10:
                        print("\n✨ Silence Detected. Processing...")
                        result = await process_buffer(audio_buffer, client_rate, processor, mode, t_start_override=None)
                        if result: await websocket.send_json(result)
                        audio_buffer = []
                        silence_chunks = 0
            
            elif "text" in message:
                if message["text"] == "STOP":
                    
                    t_stop_start = time.time() 
                    
                    print("\n🛑 STOP received. Processing remaining buffer...")
                    if len(audio_buffer) > 3:
                        result = await process_buffer(audio_buffer, client_rate, processor, mode, t_start_override=t_stop_start)
                        if result: await websocket.send_json(result)
                    
                    await websocket.close()
                    break

    except WebSocketDisconnect:
        print("\n❌ Client Disconnected")
    except Exception as e:
        print(f"\nError: {e}")