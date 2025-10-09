"use client"

import { useState } from "react"

export default function Composer({ onSend, sending }) {
  const [text, setText] = useState("")
  const [userId] = useState(() => {
    const k = "anonUserId"
    let v = typeof window !== "undefined" ? localStorage.getItem(k) : null
    if (!v) {
      v = String(Math.floor(1000 + Math.random() * 9000))
      try {
        localStorage.setItem(k, v)
      } catch {}
    }
    return v || "1001"
  })

  function submit(e) {
    e.preventDefault()
    if (!text.trim() || sending) return
    onSend({ user_id: Number(userId), text: text.trim() })
      .then(() => setText(""))
      .catch(() => {})
  }

  return (
    <form onSubmit={submit} className="flex items-center gap-2">
      <div className="rounded-md border border-neutral-800 px-2 py-2 text-xs text-neutral-400">You: User {userId}</div>
      <input
        aria-label="Message"
        className="flex-1 rounded-md border border-neutral-800 bg-transparent px-3 py-2 text-sm"
        placeholder="Type a message…"
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <button type="submit" className="btn btn-accent" disabled={sending}>
        {sending ? "Sending…" : "Send"}
      </button>
    </form>
  )
}
