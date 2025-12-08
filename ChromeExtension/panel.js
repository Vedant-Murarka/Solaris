let socket;
let audioContext;
let processor;
let input;
let globalStream;
let isRecording = false;

// DOM Elements
const startBtn = document.getElementById('startBtn');
const copyBtn = document.getElementById('copyBtn');
const status = document.getElementById('status');
const rawText = document.getElementById('rawText');
const cleanText = document.getElementById('cleanText');
const logs = document.getElementById('logs');
const toneSelect = document.getElementById('toneSelect');

// --- EVENT LISTENERS ---
startBtn.addEventListener('click', () => {
    if (!isRecording) start();
    else stop();
});

copyBtn.addEventListener('click', () => {
    const textToCopy = cleanText.innerText;
    if (textToCopy) {
        navigator.clipboard.writeText(textToCopy).then(() => {
            const originalText = copyBtn.innerText;
            copyBtn.innerText = "✅ Copied!";
            setTimeout(() => copyBtn.innerText = originalText, 1500);
        });
    }
});

// --- MAIN LOGIC ---
async function start() {
    try {
        const tone = toneSelect.value;
        
        // 1. TRY TO GET MICROPHONE PERMISSION
        try {
            globalStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        } catch (micErr) {
            alert("❌ Microphone Blocked! \n\nPlease right-click the Solaris extension icon -> Manage Extension -> Site Settings -> Allow Microphone.");
            return;
        }

        audioContext = new AudioContext();
        const sampleRate = audioContext.sampleRate;

        // 2. Connect WebSocket
        socket = new WebSocket(`ws://127.0.0.1:8000/ws?mode=${tone}&rate=${sampleRate}`);

        socket.onopen = () => {
            // Update UI
            status.innerText = "🟢 Live";
            status.classList.add("live");
            startBtn.innerText = "🛑 Finish";
            startBtn.classList.add("recording");
            toneSelect.disabled = true;
            
            // Start Audio Stream
            input = audioContext.createMediaStreamSource(globalStream);
            processor = audioContext.createScriptProcessor(2048, 1, 1);

            processor.onaudioprocess = (e) => {
                if (socket.readyState === WebSocket.OPEN) {
                    const float32Data = e.inputBuffer.getChannelData(0);
                    socket.send(float32Data);
                }
            };

            input.connect(processor);
            processor.connect(audioContext.destination);
            isRecording = true;
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === "result") {
                rawText.innerText += " " + data.raw;
                cleanText.innerText += " " + data.clean;
                logs.innerText = `⏱️ ${data.latency}ms | Clean: ${data.breakdown}`;
            }
        };

        socket.onerror = (error) => {
            console.error(error);
            alert("❌ WebSocket Error. Is your Python server running?");
            stop();
        };

        socket.onclose = () => {
            stop();
        };

    } catch (err) {
        console.error(err);
        alert("Error: " + err);
        stop();
    }
}

function stop() {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send("STOP");
    }
    
    if (globalStream) globalStream.getTracks().forEach(track => track.stop());
    if (audioContext) audioContext.close();
    
    isRecording = false;
    status.innerText = "🔴 Offline";
    status.classList.remove("live");
    startBtn.innerText = "🎙️ Record";
    startBtn.classList.remove("recording");
    toneSelect.disabled = false;
}