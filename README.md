# ⚡ Solaris Dictation Engine

### Intelligent Low-Latency Speech Dictation Assistant (Hackathon Problem Statement 4)

---

## 1. Project Overview

Solaris is a real-time speech dictation engine designed to produce clean, grammatically correct, and formatted text directly from human speech with extremely low latency ($\le 1500$ ms after pause).

This system operates entirely **offline** and relies solely on highly optimized, lightweight Machine Learning models (Small Language Models / Transformers) and classical NLP pipelines—**No external Large Language Models (LLMs) or Cloud APIs are used.**

### Key Features

* **Ultra Low Latency:** Optimized using FP16 quantization and Batch Processing to meet the critical $\le 1500$ ms processing target.
* **100% Offline:** Runs locally via a FastAPI server communicating with a Chrome Side Panel.
* **Smart Cleanup:** Automatically removes filler words (`umm`, `uh`), repetitions, and corrects run-on sentences.
* **Tone Control:** Supports Formal, Casual, Concise, and Neutral output modes.
* **Portability:** Packaged as a Chrome Extension for seamless integration into any text field (via Copy/Paste).

---

## 2. Architecture

The project follows a decoupled Client-Server architecture for maximum speed and robustness.

| Component | Technology | Role | Optimization |
| :--- | :--- | :--- | :--- |
| **Frontend** | HTML5 / JavaScript | Captures audio via MediaRecorder API, manages the WebSocket connection, handles Copy-to-Clipboard functionality. | Uses Side Panel for persistent UX. |
| **Backend** | FastAPI / Python | High-speed, asynchronous API server. | WebSockets provide minimal network latency. |
| **STT Engine** | Faster-Whisper (`base.en`) | Converts raw 16kHz audio to raw text. | **Int8 Quantization** and CTranslate2 backend. |
| **NLP Engine** | FLAN-T5 Small | Performs Grammar Correction, Punctuation/Capitalization, and Style/Tone Transfer. | **FP16 Quantization** and **Batch Processing** (parallel inference). |

---

## 3. Setup and Installation

The entire application runs from the command line after a one-time setup.

### A. Folder Structure