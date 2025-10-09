"use client";

import { Routes, Route } from "react-router-dom";
import ChatSpace from "./components/chat-space.jsx";

function App() {
  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col">
      {/* Top Navigation */}
      <header className="sticky top-0 z-10 border-b border-neutral-900 bg-neutral-950/80 backdrop-blur">
        <nav className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded bg-neutral-800" aria-hidden />
            <span className="text-base font-semibold tracking-tight">
              General Chat
            </span>
          </div>
        </nav>
      </header>

      {/* Main Content */}
      <main className="flex-grow mx-auto w-full max-w-5xl px-4 py-6">
        <Routes>
          <Route path="/" element={<ChatSpace />} />
          <Route path="*" element={<ChatSpace />} />
        </Routes>
      </main>

      {/* Footer */}
      <footer className="border-t border-neutral-900 py-6 text-center text-xs text-neutral-500">
        Built for clarity — minimal, readable, and mobile-friendly
      </footer>
    </div>
  );
}

export default App;
