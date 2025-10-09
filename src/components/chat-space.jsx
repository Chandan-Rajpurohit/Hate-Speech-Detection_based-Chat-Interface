"use client"

import useSWR from "swr"
import { useCallback, useState } from "react"
import { MessagesAPI } from "../api/client.js"
import Composer from "./composer"
import Message from "./message"

export default function ChatSpace() {
  const { data, isLoading, error, mutate } = useSWR(["messages"], () => MessagesAPI.list(), { refreshInterval: 4000 })
  const [sending, setSending] = useState(false)

  const onSend = useCallback(
    async (payload) => {
      setSending(true)
      try {
        await MessagesAPI.send(payload)
        await mutate()
      } finally {
        setSending(false)
      }
    },
    [mutate],
  )

  return (
    <main className="mx-auto max-w-5xl px-4 py-6">
      <header className="mb-6">
        <h1 className="text-pretty text-2xl font-bold">General Chat</h1>
        <p className="mt-1 text-sm text-neutral-400">Public room, no login. Toxic messages are hidden by default.</p>
      </header>

      <section className="flex min-h-[60vh] flex-col gap-6 rounded-xl border border-neutral-800 p-6">
        <div className="flex flex-col gap-6">
          {isLoading && <div className="text-base text-neutral-500">Loading…</div>}
          {error && <div className="text-base text-red-400">Failed to load</div>}
          {data?.messages?.length
            ? data.messages.map((m) => <Message key={m.id} msg={m} />)
            : !isLoading && <div className="text-base text-neutral-500">No messages yet.</div>}
        </div>
        <div className="border-t border-neutral-800 pt-6">
          <Composer onSend={onSend} sending={sending} />
        </div>
      </section>
    </main>
  )
}
