// Keep endpoints aligned with FastAPI (/api/*). Provides safe fallbacks if endpoints are missing.

import "../firebase.js" // ensure Firebase app is initialized for getAuth()
import { getAuth } from "firebase/auth"

const API_BASE = "/api"

async function authHeaders() {
  try {
    const auth = getAuth()
    const user = auth.currentUser
    if (!user) return { "Content-Type": "application/json" }
    const token = await user.getIdToken()
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    }
  } catch {
    return { "Content-Type": "application/json" }
  }
}

export async function fetchJSON(path, options = {}) {
  const headers = await authHeaders()
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...headers, ...(options.headers || {}) },
  })
  if (!res.ok) {
    // Try to read body for debugging
    const text = await res.text().catch(() => "")
    throw new Error(`API ${res.status}: ${text || res.statusText}`)
  }
  return res.json()
}

// Messages (room-aware)
export const MessagesAPI = {
  // GET /api/messages?roomId=general
  list: async (roomId = "general") => {
    try {
      const q = roomId ? `?roomId=${encodeURIComponent(roomId)}` : ""
      return await fetchJSON(`/messages${q}`)
    } catch (e) {
      console.warn("[v0] MessagesAPI.list failed:", e?.message)
      return { messages: [] }
    }
  },
  // POST /api/messages
  send: async (payload) => {
    // expected payload: { text, user_id?, roomId }
    return fetchJSON(`/messages`, {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },
}

// Optional: custom inference passthrough
export async function runCustomInference(text) {
  const res = await fetch(`${API_BASE}/custom-inference`, {
    method: "POST",
    headers: await authHeaders(),
    body: JSON.stringify({ text }),
  })
  if (!res.ok) throw new Error("Custom inference failed")
  return res.json()
}
