import os
from faster_whisper import download_model # type: ignore
from transformers import T5Tokenizer, T5ForConditionalGeneration # type: ignore

# Create a folder to store the AI brains
if not os.path.exists("models"):
    os.makedirs("models")

print("⬇️  Step 1/2: Downloading Whisper (Hearing Model)...")
# Downloads the 'base.en' model to ./models/whisper
whisper_path = download_model("base.en", output_dir="./models/whisper")
print(f"✅ Whisper saved to: {whisper_path}")

print("\n⬇️  Step 2/2: Downloading FLAN-T5 (Grammar Model)...")
model_name = "google/flan-t5-small"
save_path = "./models/t5"

# Download the model and tokenizer
tokenizer = T5Tokenizer.from_pretrained(model_name, legacy=False)
model = T5ForConditionalGeneration.from_pretrained(model_name)

# --- CRITICAL LATENCY FIX: SAVE MODEL IN FP16 (16-bit float) ---
# This significantly reduces the size and load time compared to the default FP32.
model.half().save_pretrained(save_path) 
tokenizer.save_pretrained(save_path)

print(f"✅ Grammar Model saved in FP16 format to: {save_path}")

print("\n🎉 DONE! Models are optimized for local speed.")