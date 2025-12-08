import { Routes, Route } from "react-router-dom";
import Home from "./pages/home";
import Dictation from "./pages/text";
import StoryMaker from "./pages/image";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/dictation" element={<Dictation />} />
      <Route path="/story" element={<StoryMaker />} />
    </Routes>
  );
}