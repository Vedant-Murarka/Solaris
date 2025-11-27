import { useState, useEffect, useRef } from "react";

function App() {
  const [showResults, setShowResults] = useState(false); // once true we stay on the results page
  const [isRecording, setIsRecording] = useState(false);
  const [latency, setLatency] = useState(120); // ms
  const intervalRef = useRef(null);

  useEffect(() => {
    // while recording, simulate latency changes
    if (isRecording) {
      intervalRef.current = setInterval(() => {
        // simulate latency between 50ms and 700ms
        const next = Math.round(50 + Math.random() * 650);
        setLatency(next);
      }, 400);
    } else {
      // when not recording, slowly decay latency to a baseline
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = setInterval(() => {
        setLatency((l) => {
          const next = l - Math.round((l - 40) * 0.25);
          return next < 45 ? 45 : next;
        });
      }, 600);
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isRecording]);

  const startFromLanding = () => {
    setShowResults(true);
    setIsRecording(true);
  };

  // map latency (ms) to percent for bar (0..100) treating 800ms as 100%
  const latencyPercent = Math.min(100, Math.round((latency / 800) * 100));

  return (
    <div className="min-h-screen bg-white flex flex-col items-center pt-24 px-6">
      <h1 className="text-5xl font-extrabold text-blue-400 tracking-wide mb-6">
        STT Correction
      </h1>

      {/* initial landing (only shown before first recording) */}
      {!showResults && (
        <div className="w-full max-w-2xl flex flex-col items-center gap-6">
          <div className="p-6 bg-blue-50 border border-blue-200 rounded-xl text-gray-700 shadow-sm w-full">
            <p className="text-center">
              Record your voice and get corrected STT output in real-time.
            </p>
          </div>

          <p className="text-sm text-gray-500">Press to enter voice</p>

          <button
            onClick={startFromLanding}
            className="w-full max-w-xl py-4 bg-amber-300 text-white rounded-full shadow-lg hover:bg-amber-400 transition flex items-center justify-center gap-3 text-lg"
            aria-label="Start recording"
          >
            <span className="text-2xl">🎤</span>
            <span className="font-medium">Start</span>
          </button>
        </div>
      )}

      {/* results page (shown after first recording start) */}
      {showResults && (
        <div className="w-full max-w-5xl flex flex-col gap-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-6 bg-blue-50 border border-blue-200 rounded-xl shadow-md h-64 flex flex-col">
              <h2 className="text-sm font-semibold text-blue-400 mb-3">Before</h2>
              <div className="flex-1 bg-white/0 rounded-md text-gray-700 text-sm flex items-center justify-center">
                <span className="text-gray-400">[Original STT]</span>
              </div>
            </div>

            <div className="p-6 bg-amber-50 border border-amber-200 rounded-xl shadow-md h-64 flex flex-col">
              <h2 className="text-sm font-semibold text-amber-600 mb-3">After</h2>
              <div className="flex-1 bg-white/0 rounded-md text-gray-700 text-sm flex items-center justify-center">
                <span className="text-gray-400">[Corrected Output]</span>
              </div>
            </div>
          </div>

          <div className="latency-box w-full">
            <p className="text-center text-gray-600 text-sm mb-2">Latency — {latency} ms</p>
            <div className="latency-bar">
              <div
                className="latency-fill"
                style={{ width: `${latencyPercent}%`, transition: "width 300ms ease" }}
              ></div>
            </div>
          </div>

          <div className="flex flex-col items-center gap-3">
            {/* persistent mic toggle on the results page */}
            <button
              onClick={() => setIsRecording((s) => !s)}
              className={`w-full max-w-md py-3 rounded-full shadow-md transition flex items-center justify-center gap-2 ${
                isRecording ? "bg-red-500 hover:bg-red-600 text-white" : "bg-amber-300 hover:bg-amber-400 text-white"
              }`}
              aria-pressed={isRecording}
              aria-label={isRecording ? "Stop recording" : "Start recording"}
            >
              <span className="text-2xl">{isRecording ? "⏺️" : "🎤"}</span>
              <span className="font-medium">{isRecording ? "Recording" : "Record"}</span>
            </button>

            <p className="text-xs text-gray-500">You can start/stop recording here without returning.</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;