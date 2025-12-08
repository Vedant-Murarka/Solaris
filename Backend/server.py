import numpy as np
import time
import scipy.signal
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel
from text_processor import TextProcessor

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- LOAD MODELS ---
print("⚡ Loading Whisper Model (Local)...")
model_path = "./models/whisper"
model = WhisperModel(model_path, device="cpu", compute_type="int8")

print("⚡ Loading Processor...")
processor = TextProcessor()
print("✅ Server Ready")

def resample_audio(audio_chunk_list, input_rate):
    if not audio_chunk_list:
        return np.array([], dtype=np.float32)
    audio_data = np.concatenate(audio_chunk_list)
    target_rate = 16000
    resampled_len = int(len(audio_data) * target_rate / input_rate)
    return scipy.signal.resample(audio_data, resampled_len)

async def process_buffer(audio_buffer, input_rate, processor, mode):
    if len(audio_buffer) < 5:
        return None

    t_start = time.time()
    final_audio = resample_audio(audio_buffer, input_rate)

    segments, _ = model.transcribe(
        final_audio,
        beam_size=1,
        initial_prompt="Umm, uh, like, you know.",
        condition_on_previous_text=False,
    )

    raw_text = " ".join([s.text for s in segments]).strip()

    if len(raw_text) > 1:
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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    mode = websocket.query_params.get("mode", "Neutral")
    client_rate = float(websocket.query_params.get("rate", 44100))

    print(f"\n🔌 Client Connected | Mode: {mode} | Rate: {client_rate}")

    audio_buffer = []
    silence_chunks = 0
    AMPLITUDE_THRESHOLD = 0.005
    SILENCE_LIMIT = 15

    try:
        while True:
            msg = await websocket.receive()

            # --- Binary Audio Data ---
            if "bytes" in msg and msg["bytes"] is not None:
                raw_bytes = msg["bytes"]

                try:
                    chunk = np.frombuffer(memoryview(raw_bytes), dtype=np.float32)
                except Exception as e:
                    print("❌ Audio parse error:", e)
                    continue

                vol = float(np.sqrt(np.mean(chunk.astype(np.float64) ** 2))) if chunk.size else 0.0
                print(f"📊 Volume: {vol:.4f} | Buffer chunks: {len(audio_buffer)} | Samples: {chunk.size}")

                if vol > AMPLITUDE_THRESHOLD:
                    silence_chunks = 0
                    audio_buffer.append(chunk)
                else:
                    if len(audio_buffer) > 0:
                        silence_chunks += 1
                        audio_buffer.append(chunk)

                    if silence_chunks > SILENCE_LIMIT and len(audio_buffer) > 10:
                        print("\n✨ Silence detected → Processing...")
                        result = await process_buffer(audio_buffer, client_rate, processor, mode)
                        if result:
                            await websocket.send_json(result)
                        audio_buffer = []
                        silence_chunks = 0

            # --- Stop Command ---
            elif "text" in msg and msg["text"] == "STOP":
                print("🛑 STOP received → Final processing")
                if len(audio_buffer) > 3:
                    result = await process_buffer(audio_buffer, client_rate, processor, mode)
                    if result:
                        await websocket.send_json(result)
                await websocket.close()
                break

    except WebSocketDisconnect:
        print("❌ Client Disconnected")