"use client"

import { useState } from "react"

function EyeIcon({ className = "h-4 w-4" }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path
        fill="currentColor"
        d="M12 5c5 0 9 5 9 7s-4 7-9 7-9-5-9-7 4-7 9-7zm0 2C8 7 4.9 10.2 4 12c.9 1.8 4 5 8 5s7.1-3.2 8-5c-.9-1.8-4-5-8-5zm0 2.5a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9z"
      ></path>
    </svg>
  )
}

function FlagIcon({ className = "h-4 w-4" }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path fill="currentColor" d="M6 3h12l-1.5 4L18 11H8v10H6V3z"></path>
    </svg>
  )
}

export default function Message({ msg }) {
  const [revealed, setRevealed] = useState(false)
  const isToxic = !!msg.is_toxic

  return (
    <div className="flex gap-3">
      <div className="h-8 w-8 shrink-0 rounded-full bg-neutral-800" aria-hidden="true" />
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm text-neutral-400">User {msg.user_id}</span>
          {isToxic && (
            <span className="rounded-md bg-neutral-800 px-2 py-0.5 text-xs text-[color:var(--color-accent)]">
              Toxic
            </span>
          )}
        </div>

        {/* Bubble */}
        <div className="mt-1 overflow-hidden rounded-card border border-neutral-800 bg-[color:var(--color-muted)]">
          {!isToxic || revealed ? (
            <p className="p-3 text-sm text-[color:var(--color-fg)]">{msg.text}</p>
          ) : (
            <>
              {/* Hidden state: keep bubble background but blank content */}
              <div className="p-3 text-sm text-neutral-500 select-none">
                {"Message hidden due to detected toxicity."}
              </div>
              <div className="flex items-center gap-2 border-t border-neutral-800 bg-black/20 px-2 py-1.5">
                <button
                  type="button"
                  className="btn btn-ghost text-xs"
                  onClick={() => setRevealed(true)}
                  aria-label="Reveal message"
                >
                  <EyeIcon />
                  Reveal
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
