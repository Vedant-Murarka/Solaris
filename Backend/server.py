import numpy as np
import time
import scipy.signal
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from faster_whisper import WhisperModel

# Ensure text_processor.py is in the same folder
from text_processor import TextProcessor

app = FastAPI()

# --- 1. LOAD MODELS (OFFLINE) ---
print("⚡ Loading Whisper Model (Local)...")
model_path = "./models/whisper"

try:
    # 'int8' is critical for low latency on CPU
    model = WhisperModel(model_path, device="cpu", compute_type="int8")
except Exception as e:
    print(f"❌ ERROR Loading Whisper: {e}")
    print("   -> Did you run 'python setup_models.py'?")
    raise

print("⚡ Loading Processor...")
processor = TextProcessor()
print("✅ Server Ready. Open http://127.0.0.1:8000")

# --- 2. SERVE UI ---
@app.get("/")
async def get():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# --- 3. HELPER FUNCTIONS ---
def resample_audio(audio_chunk_list, input_rate):
    """Resamples browser audio (e.g., 48k) to Whisper's required 16k."""
    if not audio_chunk_list:
        return np.array([], dtype=np.float32)
    
    audio_data = np.concatenate(audio_chunk_list)
    target_rate = 16000
    
    num_samples = int(len(audio_data) * float(target_rate) / input_rate)
    resampled_data = scipy.signal.resample(audio_data, num_samples)
    return resampled_data

async def process_buffer(audio_buffer, input_rate, processor, mode):
    """Transcribes and Cleans a chunk of audio."""
    if len(audio_buffer) < 5: return None 

    t_start = time.time()
    
    # 1. Resample
    final_audio = resample_audio(audio_buffer, input_rate)
    
    # 2. Transcribe
    # 'initial_prompt': Forces Whisper to recognize fillers in the raw text
    # 'condition_on_previous_text=False': Prevents hallucinations/loops
    segments, _ = model.transcribe(
        final_audio, 
        beam_size=1, 
        initial_prompt="Umm, uh, like, you know, okay.", 
        condition_on_previous_text=False
    )
    raw_text = " ".join([s.text for s in segments]).strip()
    
    if len(raw_text) > 1:
        # 3. Clean & Tone
        final_text, stats = processor.process(raw_text, mode)
        total_latency = (time.time() - t_start) * 1000
        
        return {
            "type": "result",
            "raw": raw_text,
            "clean": final_text,
            "latency": f"{total_latency:.0f}",
            "breakdown": f"Clean:{stats['cleaning_ms']:.0f} | Gram:{stats['grammar_ms']:.0f}"
        }
    return None

# --- 4. WEBSOCKET HANDLER ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Get configuration from URL
    mode = websocket.query_params.get("mode", "Neutral")
    try:
        client_rate = float(websocket.query_params.get("rate", 44100))
    except:
        client_rate = 44100.0
        
    print(f"🔌 Connected | Mode: {mode} | Input Rate: {client_rate}Hz")
    
    audio_buffer = [] 
    silence_chunks = 0
    
    # TUNING: Threshold 0.03 filters out AC/Fan noise
    SILENCE_LIMIT = 15  
    AMPLITUDE_THRESHOLD = 0.03 

    try:
        while True:
            # We use receive() to handle both Text (Commands) and Bytes (Audio)
            message = await websocket.receive()

            if "bytes" in message:
                # --- AUDIO DATA ---
                data = message["bytes"]
                chunk_np = np.frombuffer(data, dtype=np.float32)
                
                # VAD Check
                volume = np.sqrt(np.mean(chunk_np**2))
                
                if volume > AMPLITUDE_THRESHOLD:
                    # Speech
                    silence_chunks = 0
                    audio_buffer.append(chunk_np)
                else:
                    # Silence
                    if len(audio_buffer) > 0:
                        silence_chunks += 1
                        audio_buffer.append(chunk_np) 
                    
                    # Silence Trigger (Auto-process)
                    if silence_chunks > SILENCE_LIMIT and len(audio_buffer) > 10:
                        print("✨ Processing Sentence (Silence Trigger)...")
                        result = await process_buffer(audio_buffer, client_rate, processor, mode)
                        if result:
                            await websocket.send_json(result)
                        
                        audio_buffer = []
                        silence_chunks = 0
            
            elif "text" in message:
                # --- STOP COMMAND ---
                if message["text"] == "STOP":
                    print("🛑 STOP received. Processing remaining buffer...")
                    if len(audio_buffer) > 5:
                        result = await process_buffer(audio_buffer, client_rate, processor, mode)
                        if result:
                            await websocket.send_json(result)
                    
                    await websocket.close()
                    break

    except WebSocketDisconnect:
        print("❌ Client Disconnected")
    except Exception as e:
        print(f"Error: {e}")