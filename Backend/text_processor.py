import re
import time
from transformers import T5Tokenizer, T5ForConditionalGeneration # type: ignore

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

            self.model = T5ForConditionalGeneration.from_pretrained(
                self.model_path,
                local_files_only=True
            )

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
        clean_text = re.sub(
            r'\b(\w+)( \1\b)+',
            r'\1',
            clean_text,
            flags=re.IGNORECASE
        )

        stats["cleaning_ms"] = (time.time() - t0) * 1000

        # --- PHASE 2: AI Grammar Correction (Deterministic) ---
        t1 = time.time()

        sentences = self.split_sentences(clean_text)

        if not sentences:
            return "", stats

        prompts = []

        for sent in sentences:
            prompts.append(f"""
You are a speech transcript cleaner.

RULES:
- DO NOT add any new information.
- DO NOT change the meaning or intent.
- Remove filler words ONLY if they do not affect meaning.
- Fix grammar and spacing MINIMALLY.
- Keep original tone and phrasing.
- Keep sentences short, direct, and natural.
- Output only the cleaned text.

Text: "{sent}"

Cleaned:
""")

        inputs = self.tokenizer(
            prompts,
            return_tensors="pt",
            padding=True,
            truncation=True
        )

        # STRICT NO-HALLUCINATION SETTINGS
        outputs = self.model.generate(
            inputs.input_ids,
            max_new_tokens=128,
            num_beams=1,
            do_sample=False,   # No randomness
            temperature=0.0,   # Fully deterministic
            repetition_penalty=1.0
        )

        corrected_sentences = self.tokenizer.batch_decode(
            outputs,
            skip_special_tokens=True
        )
        final_text = " ".join(corrected_sentences)

        stats["grammar_ms"] = (time.time() - t1) * 1000
        stats["total_ms"] = (time.time() - t_start) * 1000

        return final_text, stats
