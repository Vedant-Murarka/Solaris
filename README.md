# 🎙️ Solaris Dictation Engine: Intelligent, Offline Speech Processing

**Solaris** is a high-performance, fully offline dictation application engineered to produce clean, grammatically correct, and formatted text directly from speech with extremely low latency. It operates entirely **offline** and relies solely on highly optimized, lightweight Machine Learning models (Small Transformers).

---

## ✨ Features & Engineering Highlights

| Feature | Description |
| :--- | :--- |
| **Ultra Low Latency** | Optimized using **FP16 quantization** and **Batch Processing** to reduce computational time on the CPU. |
| **100% Offline** | Runs locally via a FastAPI server, ensuring **maximum data privacy** and no reliance on external cloud APIs. |
| **Tone Control** | Supports **Formal, Neutral, and Casual** modes for specific output styles (e.g., expanding contractions for Formal mode). |
| **Smart Cleanup** | Automatically removes filler words ('umm,' 'uh'), repetitions, and corrects run-on sentences. |
| **Robust Audio** | Features Sample Rate Correction and VAD (Voice Activity Detection) tuning for stable input from diverse sources. |

---

## ⚙️ System Architecture

Solaris uses a Client-Server architecture running entirely on the local machine:

1.  **Frontend (React/Chrome Extension):** Captures audio and sends selected tone/mode data.
2.  **Transport:** Audio data is streamed via **WebSockets** for low-latency, real-time transfer.
3.  **Backend (FastAPI):** Orchestrates the three-stage processing pipeline:
    * **Stage 1: Transcription:** `Faster-Whisper` (Int8) handles initial STT.
    * **Stage 2: Pre-Processing/Contraction Fix:** Custom **Python Regex** handles mode-specific filler removal and guaranteed contraction expansion.
    * **Stage 3: Grammar/Style Correction:** **FLAN-T5 Small** (FP16) applies sophisticated style transfer, punctuation, and grammar fixes.

---

## 🚀 Getting Started

This project requires setting up two distinct components: the **Backend API Server (Python)** and the **Frontend (React/Chrome Extension)**.

### Prerequisites

You need Python 3.9+ and Node.js/npm installed on your system.

1.  **Clone the repository:**
    ```bash
    git clone [Your Repository URL]
    cd Solaris
    ```

### 1. Backend Server Setup (Python)

This sets up the FastAPI server, the T5 Grammar Engine, and the Whisper STT model.

1.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Model Setup:** Download the required models and quantize them for local speed.
    ```bash
    cd Backend
    python setup_models.py
    cd ..
    ```

4.  **Run the Backend Server:** (Keep this running in a separate terminal window.)
    ```bash
    cd Backend
    uvicorn server:app --reload
    ```
    *The server will run on `http://127.0.0.1:8000`.*

### 2. Frontend / Extension Setup (React)

This sets up the user interface (UI) for the Chrome Side Panel.

1.  **Install Frontend Dependencies:**
    ```bash
    cd TCSSFrontend
    npm install
    npm install react-router-dom
    ```

2.  **Build the Project:** Run the build command. This creates the production-ready files needed by the browser.
    ```bash
    npm run dev
    ```

### 3. Loading the Extension in Chrome

1.  Open Chrome or Edge and navigate to `chrome://extensions`.
2.  Enable **Developer mode** (top right toggle).
3.  Click **Load unpacked**.
4.  Select the **built folder** (usually named `dist` or `build`) located inside your `Solaris/TCSSFrontend` directory.
5.  Pin the extension, open the side panel, and ensure the server is running to establish the WebSocket connection.
