import os
from faster_whisper import download_model
from transformers import T5Tokenizer, T5ForConditionalGeneration

# Create a folder to store the AI brains
if not os.path.exists("models"):
    os.makedirs("models")

print("⬇️  Step 1/2: Downloading Whisper (Hearing Model)...")
# This downloads the 'base.en' model to the ./models/whisper folder
whisper_path = download_model("base.en", output_dir="./models/whisper")
print(f"✅ Whisper saved to: {whisper_path}")

print("\n⬇️  Step 2/2: Downloading FLAN-T5 (Grammar Model)...")
model_name = "google/flan-t5-small"
save_path = "./models/t5"

# Download and save to ./models/t5
tokenizer = T5Tokenizer.from_pretrained(model_name, legacy=False)
model = T5ForConditionalGeneration.from_pretrained(model_name)

tokenizer.save_pretrained(save_path)
model.save_pretrained(save_path)
print(f"✅ Grammar Model saved to: {save_path}")

print("\n🎉 DONE! You can now disconnect the internet.")