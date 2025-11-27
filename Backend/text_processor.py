import re
import time
from transformers import T5Tokenizer, T5ForConditionalGeneration

class TextProcessor:
    def __init__(self):
        print("⚡ Loading FLAN-T5 (Grammar & Tone Engine)...")
        
        # OFFLINE PATH: Points to the folder created by setup_models.py
        self.model_path = "./models/t5" 
        
        try:
            self.tokenizer = T5Tokenizer.from_pretrained(self.model_path, local_files_only=True, legacy=False)
            self.model = T5ForConditionalGeneration.from_pretrained(self.model_path, local_files_only=True)
        except OSError:
            print("❌ ERROR: Grammar models not found in ./models/t5")
            print("   -> Please run 'python setup_models.py' first!")
            raise
        
        # Regex to strip obvious fillers (Removed 'like' so AI handles it contextually)
        self.filler_pattern = r"\b(umm+|uhh+|uh|um|you know|matlab|hmm+)\b"

    def remove_fillers(self, text):
        """Step 1: Remove obvious non-words via Regex (Zero Latency)."""
        return re.sub(self.filler_pattern, "", text, flags=re.IGNORECASE)

    def clean_punctuation(self, text):
        """Step 2: Fix the dots/commas left behind by removal."""
        # 1. Fix double dots ".." or ". ." -> "."
        text = re.sub(r'\.{2,}', '.', text)
        # 2. Fix "Word . , Next" -> "Word. Next"
        text = re.sub(r'([.?!])\s*,', r'\1', text)
        # 3. Fix "Word , ." -> "Word."
        text = re.sub(r',\s*([.?!])', r'\1', text)
        # 4. Remove floating punctuation at start
        text = re.sub(r'^\s*[,.]\s*', '', text)
        # 5. Fix multiple spaces
        return " ".join(text.split())

    def split_sentences(self, text):
        """
        Splits text carefully so the AI doesn't skip middle sentences.
        Splits on '.', '?', '!' followed by space.
        """
        parts = re.split(r'(?<=[.?!])\s+', text)
        return [p.strip() for p in parts if len(p.strip()) > 1]

    def process(self, raw_text, tone_mode="Neutral"):
        stats = {}
        t_start = time.time()

        # --- PHASE 1: CLEANING (Zero Latency) ---
        t0 = time.time()
        
        # 1. Remove fillers
        clean_text = self.remove_fillers(raw_text)
        # 2. Fix punctuation
        clean_text = self.clean_punctuation(clean_text)
        # 3. Fix repetition (e.g., "very very" -> "very")
        clean_text = re.sub(r'\b(\w+)( \1\b)+', r'\1', clean_text, flags=re.IGNORECASE)
        
        stats['cleaning_ms'] = (time.time() - t0) * 1000

        # --- PHASE 2: BATCHED AI PROCESSING (Latency Optimized) ---
        t1 = time.time()
        
        sentences = self.split_sentences(clean_text)
        
        # If input was just noise/fillers, return empty
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

        # 2. Tokenize ALL sentences at once (Batching)
        inputs = self.tokenizer(prompts, return_tensors="pt", padding=True, truncation=True)
        
        # 3. Generate ALL outputs at once (Fastest Method)
        outputs = self.model.generate(
            inputs.input_ids, 
            max_new_tokens=64, 
            temperature=0.3,
            do_sample=True
        )
        
        # 4. Decode Batch
        corrected_sentences = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
        
        # Rejoin into final paragraph
        final_text = " ".join(corrected_sentences)
        
        stats['grammar_ms'] = (time.time() - t1) * 1000
        stats['total_ms'] = (time.time() - t_start) * 1000
        
        return final_text, stats