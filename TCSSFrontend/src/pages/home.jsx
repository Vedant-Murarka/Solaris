import { useNavigate } from "react-router-dom";
import { Mic, Image } from "lucide-react";

export default function Home() {
  const nav = useNavigate();

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden">

      {/* Optional Gradient Behind Everything */}
      <div className="absolute inset-0 -z-10 bg-gradient-to-br from-blue-200 to-blue-100 animate-[pulse_5s_infinite] opacity-60"></div>

      <div className="relative z-10 bg-white p-10 rounded-3xl shadow-2xl text-center w-full max-w-lg border border-blue-200">

        <h1 className="text-5xl font-extrabold text-blue-700 mb-6 drop-shadow-lg">
          🌞 Solaris
        </h1>

        <p className="text-gray-600 mb-10 text-lg">Choose a feature to continue</p>

        <button
          className="w-full bg-blue-600 hover:bg-blue-700 text-white py-4 rounded-xl mb-4 flex items-center justify-center gap-2 text-lg font-semibold shadow-lg"
          onClick={() => nav("/dictation")}
        >
          <Mic size={20} /> Speech-to-Text Dictation
        </button>

        <button
          className="w-full bg-green-600 hover:bg-green-700 text-white py-4 rounded-xl flex items-center justify-center gap-2 text-lg font-semibold shadow-lg"
          onClick={() => nav("/story")}
        >
          <Image size={20} /> Storytelling with Pictures
        </button>
      </div>
    </div>
  );
}
