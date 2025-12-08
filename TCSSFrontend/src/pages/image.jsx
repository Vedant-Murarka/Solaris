import { useState } from "react";
import { Mic, Square } from "lucide-react";

export default function StoryMaker() {
  const [isRecording, setIsRecording] = useState(false);
  const [story, setStory] = useState("");
  const [imageUrl, setImageUrl] = useState("");

  const toggleStoryRecord = () => {
    if (!isRecording) {
      setStory("🎤 Listening for your story...");
    } else {
      setStory("Once upon a time, there was a brave cat who explored space...");
      setImageUrl("https://picsum.photos/400/300?random=" + Date.now());
    }
    setIsRecording(!isRecording);
  };

  return (
    <div className="relative min-h-screen bg-blue-100 flex items-center justify-center p-8 overflow-hidden">

      {/* Tailwind Animated Background */}
      <div className="absolute inset-0 z-0 bg-gradient-to-br from-blue-200 to-blue-100 animate-[pulse_6s_ease-in-out_infinite] opacity-60"></div>

      <div className="relative z-10 bg-white w-full max-w-xl p-8 rounded-3xl shadow-xl border border-blue-200">
        <h1 className="text-3xl font-bold text-blue-700 mb-4 drop-shadow">
          🖼 Storytelling from Voice
        </h1>

        <button
          onClick={toggleStoryRecord}
          className={`px-5 py-3 rounded-xl text-white font-semibold flex items-center gap-2 shadow-md ${
            isRecording ? "bg-red-600" : "bg-blue-600"
          }`}
        >
          {isRecording ? <Square size={18} /> : <Mic size={18} />}
          {isRecording ? "Stop Recording" : "Start Story Recording"}
        </button>

        <div className="mt-6 bg-blue-50 rounded-xl p-4 min-h-[120px]">
          <p className="text-gray-800 whitespace-pre-wrap">{story}</p>
        </div>

        {imageUrl && (
          <div className="mt-6">
            <img
              src={imageUrl}
              className="rounded-xl shadow-md border"
              alt="Generated Story"
            />
          </div>
        )}
      </div>
    </div>
  );
}
