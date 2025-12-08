import { useState, useRef, useEffect } from "react";
import { Clipboard, Mic, Square, ChevronDown } from "lucide-react";

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [tone, setTone] = useState("Neutral");
  const [raw, setRaw] = useState("");
  const [clean, setClean] = useState("");
  const [latencyLogs, setLatencyLogs] = useState([]);

  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const processorRef = useRef(null);
  const sourceRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  const toggleRecord = async () => {
    if (!isRecording) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamRef.current = stream;

        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        audioContextRef.current = audioContext;

        const source = audioContext.createMediaStreamSource(stream);
        sourceRef.current = source;

        const processor = audioContext.createScriptProcessor(4096, 1, 1);
        processorRef.current = processor;

        // BACKEND-COMPATIBLE WS URL
        const wsUrl = `ws://localhost:8000/ws?mode=${tone}&rate=${audioContext.sampleRate}`;
        console.log("🔌 Connecting:", wsUrl);

        wsRef.current = new WebSocket(wsUrl);
        wsRef.current.binaryType = "arraybuffer";

        wsRef.current.onmessage = (event) => {
          try {
            const result = JSON.parse(event.data);

            // Append raw + cleaned text
            if (result.raw) setRaw((prev) => prev + " " + result.raw);
            if (result.clean) setClean((prev) => prev + " " + result.clean);

            // Latency logs
            if (result.latency) {
              setLatencyLogs((prev) => [
                ...prev,
                `${result.latency}ms - ${result.breakdown}`,
              ]);
            }
          } catch (err) {
            console.error("JSON parse error:", err);
          }
        };

        processor.onaudioprocess = (event) => {
          const audioData = event.inputBuffer.getChannelData(0);
          if (wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(audioData.buffer);
          }
        };

        source.connect(processor);
        processor.connect(audioContext.destination);

        // Reset logs + text
        setIsRecording(true);
        setRaw("");
        setClean("");
        setLatencyLogs([]);
      } catch (err) {
        alert("Microphone access denied");
      }
    } else {
      // STOP recording and WS
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send("STOP");
      }

      if (sourceRef.current) sourceRef.current.disconnect();
      if (processorRef.current) processorRef.current.disconnect();
      if (audioContextRef.current) audioContextRef.current.close();
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }

      setIsRecording(false);
    }
  };

  const copyCleaned = async () => {
    if (!clean) return alert("Nothing to copy");
    await navigator.clipboard.writeText(clean);
    alert("Copied!");
  };

  const tones = ["Neutral", "Formal", "Friendly", "Strict", "Enthusiastic"];

  return (
    <div className="min-h-screen w-full bg-blue-100 flex justify-center py-10 px-4">
      <div className="w-full max-w-5xl bg-white rounded-3xl shadow-2xl p-10 border border-blue-200">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-4xl font-bold text-blue-700">🎙 Solaris Dictation</h1>

          {/* Tone Selector */}
          <div className="relative">
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="appearance-none bg-blue-50 text-blue-700 px-4 py-2 rounded-xl border border-blue-300 font-medium shadow-sm cursor-pointer"
            >
              {tones.map((t) => (
                <option key={t} value={t}>
                  {t} Tone
                </option>
              ))}
            </select>
            <ChevronDown
              size={18}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-blue-700"
            />
          </div>
        </div>

        {/* Record Button */}
        <button
          onClick={toggleRecord}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl text-white font-semibold transition-all shadow-md ${
            isRecording
              ? "bg-red-600 hover:bg-red-700"
              : "bg-blue-600 hover:bg-blue-700"
          }`}
        >
          {isRecording ? <Square size={18} /> : <Mic size={18} />}
          {isRecording ? "Stop Recording" : "Start Recording"}
        </button>

        {/* Two-Column Output */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-8">
          {/* Raw Box */}
          <div className="bg-white border border-blue-100 rounded-2xl p-5 shadow-sm">
            <h3 className="font-bold text-blue-700 mb-2">Raw Input</h3>
            <div className="min-h-[200px] text-sm whitespace-pre-wrap text-gray-700">
              {raw}
            </div>
          </div>

          {/* Clean Output */}
          <div className="bg-green-50 border border-green-200 rounded-2xl p-5 shadow-sm">
            <h3 className="font-bold text-green-700 mb-2">Cleaned Output</h3>
            <div className="min-h-[200px] text-sm text-green-800 whitespace-pre-wrap">
              {clean}
            </div>

            <button
              onClick={copyCleaned}
              className="mt-3 flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg shadow"
            >
              <Clipboard size={16} /> Copy
            </button>
          </div>
        </div>

        {/* Latency Logs */}
        <div className="mt-10 bg-gray-100 p-5 rounded-2xl text-xs font-mono shadow-inner">
          <h3 className="font-bold text-gray-700 mb-2">Latency Logs</h3>
          <div className="space-y-1">
            {latencyLogs.map((l, i) => (
              <div key={i}>{l}</div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;