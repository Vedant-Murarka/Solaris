import re
import time
from transformers import T5Tokenizer, T5ForConditionalGeneration

class TextProcessor:
    def __init__(self):
        print("⚡ Loading FLAN-T5 (Grammar & Tone Engine)...")
        
        self.model_path = "./models/t5" 
        
        try:
            self.tokenizer = T5Tokenizer.from_pretrained(self.model_path, local_files_only=True, legacy=False)
            
            # --- REVERT: Load the model in full precision (FP32) ---
            # The .half() method has been removed.
            self.model = T5ForConditionalGeneration.from_pretrained(self.model_path, local_files_only=True)
            
        except OSError:
            print("❌ ERROR: Grammar models not found in ./models/t5")
            print("   -> Did you re-run 'python setup_models.py'?")
            raise
        
        self.filler_pattern = r"\b(umm+|uhh+|uh|um|you know|matlab|hmm+)\b"

    def remove_fillers(self, text):
        """Step 1: Remove obvious non-words via Regex (Zero Latency)."""
        return re.sub(self.filler_pattern, "", text, flags=re.IGNORECASE)

    def clean_punctuation(self, text):
        """Step 2: Fix the dots/commas/spaces left behind."""
        
        text = re.sub(r'\.{2,}', '.', text)
        text = re.sub(r',\s*,', ',', text)
        text = re.sub(r'([.?!])\s*,', r'\1', text)
        text = re.sub(r',\s*([.?!])', r'\1', text)
        text = re.sub(r'^\s*[,.]\s*', '', text)
        return " ".join(text.split())

    def split_sentences(self, text):
        """Splits text into a list for processing."""
        parts = re.split(r'(?<=[.?!])\s+', text)
        return [p.strip() for p in parts if len(p.strip()) > 1]

    def process(self, raw_text, tone_mode="Neutral"):
        stats = {}
        t_start = time.time()

        # --- PHASE 1: CLEANING (Zero Latency) ---
        t0 = time.time()
        
        clean_text = self.remove_fillers(raw_text)
        clean_text = self.clean_punctuation(clean_text)
        clean_text = re.sub(r'\b(\w+)( \1\b)+', r'\1', clean_text, flags=re.IGNORECASE)
        
        stats['cleaning_ms'] = (time.time() - t0) * 1000

        # --- PHASE 2: BATCHED AI PROCESSING (Latency Optimized) ---
        t1 = time.time()
        
        sentences = self.split_sentences(clean_text)
        
        if not sentences:
            return "", stats

        # 1. Prepare Prompts (Batch Preparation)
        prompts = []
        for sent in sentences:
            if tone_mode == "Formal":
                prompts.append(f"Make formal: {sent}")
            elif tone_mode == "Concise":
                prompts.append(f"Make concise: {sent}")
            elif tone_mode == "Casual":
                prompts.append(f"Make casual: {sent}")
            else:
                prompts.append(f"Fix grammar: {sent}")

        # 2. Tokenize ALL sentences at once (Batching is the latency saver)
        inputs = self.tokenizer(prompts, return_tensors="pt", padding=True, truncation=True)
        
        # 3. Generate ALL outputs at once 
        outputs = self.model.generate(
            inputs.input_ids, 
            max_new_tokens=64, 
            temperature=0.3,
            do_sample=True
        )
        
        # 4. Decode Batch and Rejoin
        corrected_sentences = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
        final_text = " ".join(corrected_sentences)
        
        stats['grammar_ms'] = (time.time() - t1) * 1000
        stats['total_ms'] = (time.time() - t_start) * 1000
        
        return final_text, stats