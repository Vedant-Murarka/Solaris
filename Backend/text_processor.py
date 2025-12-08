import re
import time
from transformers import T5Tokenizer, T5ForConditionalGeneration # type: ignore
import torch # Required for .half() and model loading

class TextProcessor:
    def __init__(self):
        print("⚡ Loading FLAN-T5 (Grammar & Tone Engine)...")

        self.model_path = "./models/t5"

        try:
            self.tokenizer = T5Tokenizer.from_pretrained(
                self.model_path,
                local_files_only=True,
                legacy=False
            )

            # CRITICAL FIX: Load the model in half-precision (FP16)
            # This ensures speed and proper model behavior for the weights saved by setup_models.py.
            self.model = T5ForConditionalGeneration.from_pretrained(
                self.model_path,
                local_files_only=True
            ).half() 

        except OSError:
            print("❌ ERROR: Grammar models not found in ./models/t5")
            print("   -> Did you re-run 'python setup_models.py'?")
            raise

        # Define the patterns for simple non-word disfluencies (for Neutral/Formal modes)
        self.disfluency_pattern = r"\b(umm+|uhh+|uh|um|you know|matlab|hmm+)\b"


    # -------------------------------------------
    # CLEANING PHASE UTILITIES
    # -------------------------------------------

    def clean_punctuation(self, text):
        """Fix the dots/commas/spaces left behind."""
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
    
    # -------------------------------------------
    # FORMAL MODE ENFORCEMENT
    # -------------------------------------------
    
    def enforce_formal_cleanup(self, text):
        """
        Enforces expansion of common informal contractions for Formal mode only.
        (Guaranteed fix for 'gonna' -> 'going to', etc.)
        """
        if not text:
            return ""
        
        # 1. Expand contractions 
        text = re.sub(r"\b(gonna)\b", "going to", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(wanna)\b", "want to", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(kinda)\b", "kind of", text, flags=re.IGNORECASE)

        # 2. Clean up resulting double spaces
        return " ".join(text.split())


    # -------------------------------------------
    # MAIN PROCESS FUNCTION
    # -------------------------------------------

    def process(self, raw_text, tone_mode="Neutral"):
        stats = {}
        t_start = time.time()

        # ----------------------------
        # PHASE 1: CLEANING (Mode-Specific)
        # ----------------------------
        t0 = time.time()

        # Start with the raw input text
        text_for_t5 = raw_text 

        # --- 1. MODE-SPECIFIC PRE-PROCESSING ---
        
        # A. Remove simple disfluencies (umm, uh) for Neutral and Formal (Casual preserves them)
        if tone_mode in ["Neutral", "Formal"]:
            # Use the defined disfluency pattern
            text_for_t5 = re.sub(self.disfluency_pattern, "", text_for_t5, flags=re.IGNORECASE)
        
        # B. Enforce formal standards (contractions) only for Formal
        if tone_mode == "Formal":
            text_for_t5 = self.enforce_formal_cleanup(text_for_t5)

        # C. Apply final structural cleanup (applies to all modes)
        text_for_t5 = self.clean_punctuation(text_for_t5)
        # Remove duplicated words
        text_for_t5 = re.sub(r'\b(\w+)( \1\b)+', r'\1', text_for_t5, flags=re.IGNORECASE)

        stats["cleaning_ms"] = (time.time() - t0) * 1000

        # ----------------------------
        # PHASE 2: T5 GRAMMAR FIX (Mode-Specific Prompt)
        # ----------------------------
        t1 = time.time()

        sentences = self.split_sentences(text_for_t5)

        if not sentences:
            return "", stats

        # Define instruction set based on the three modes
        instruction_map = {
            # 1. Neutral: Uses a clear, direct instruction structure.
            "Neutral": "Correct grammar and remove conversational fillers from the text: ",
            
            # 2. Formal: Uses the strong structure to enforce formal style and fixes.
            "Formal": "Rewrite the text formally, fixing grammar, removing contractions, shorthand, and unnecessary conversational phrases: ",
            
            # 3. Casual: Uses a simple structure to fix grammar but PRESERVES style.
            "Casual": "Fix the grammar and punctuation in the text. Do not change the informal style or remove fillers: ",
        }
        
        instruction = instruction_map.get(tone_mode, instruction_map["Neutral"])

        prompts = []
        for sent in sentences:
            # New, simpler template structure (Removes the confusing final quotes from the prompt itself)
            prompts.append(f"{instruction} {sent}") # No quotes around {sent} in the prompt

        inputs = self.tokenizer(
            prompts,
            return_tensors="pt",
            padding=True,
            truncation=True
        )
        
        # Move inputs to the correct device (CPU/GPU) if needed. If only running on CPU, this is fine.
        # inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        outputs = self.model.generate(
            inputs.input_ids,
            max_new_tokens=64,
            num_beams=1,
            do_sample=False, 
            temperature=0.0, 
            repetition_penalty=1.0
        )

        # ----------------------------
        # PHASE 3: FINAL DECODE & CLEANUP
        # ----------------------------
        
        corrected_sentences = self.tokenizer.batch_decode(
            outputs, skip_special_tokens=True
        )

        cleaned_output_parts = []
        for sentence in corrected_sentences:
            # 1. Strip external quotes/whitespace (Fixes the quote issue)
            sentence = sentence.strip().strip('"')
            
            # 2. Ensure the sentence starts with a capital letter (Fixes capitalization)
            if sentence:
                sentence = sentence[0].upper() + sentence[1:]
                
            cleaned_output_parts.append(sentence)
        
        final_text = " ".join(cleaned_output_parts)

        stats["grammar_ms"] = (time.time() - t1) * 1000
        stats["total_ms"] = (time.time() - t_start) * 1000

        return final_text, stats