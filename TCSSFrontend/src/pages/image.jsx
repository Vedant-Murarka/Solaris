import { useState } from "react";
import { Mic, Square } from "lucide-react";

export default function StoryMaker() {
  const [isRecording, setIsRecording] = useState(false);
  const [story, setStory] = useState("");
  const [imageUrl, setImageUrl] = useState("");

  const toggleStoryRecord = () => {
    if (!isRecording) {
      // later: connect to story backend
      setStory("🎤 Listening for your story...");
    } else {
      // fake output (placeholder)
      setStory("Once upon a time, there was a brave cat who explored space...");
      setImageUrl("https://picsum.photos/400/300?random=" + Date.now());
    }
    setIsRecording(!isRecording);
  };

  return (
    <div className="min-h-screen bg-purple-100 flex items-center justify-center p-8">
      <div className="bg-white w-full max-w-xl p-8 rounded-3xl shadow-xl border border-purple-200">

        <h1 className="text-3xl font-bold text-purple-700 mb-4">
          🖼 Storytelling from Voice
        </h1>

        <button
          onClick={toggleStoryRecord}
          className={`px-5 py-3 rounded-xl text-white font-semibold flex items-center gap-2 ${
            isRecording ? "bg-red-600" : "bg-purple-600"
          }`}
        >
          {isRecording ? <Square size={18} /> : <Mic size={18} />}
          {isRecording ? "Stop Recording" : "Start Story Recording"}
        </button>

        <div className="mt-6 bg-purple-50 rounded-xl p-4 min-h-[120px]">
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