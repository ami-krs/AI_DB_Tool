"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useDbConfig } from "@/lib/db-config";
import { chat, getSchema } from "@/lib/api";
import type { SchemaResponse } from "@/lib/types";

export default function ChatPage() {
  const { dbConfig, isConnected } = useDbConfig();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; content: string; sql?: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [schemaContext, setSchemaContext] = useState<Record<string, unknown> | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isConnected && dbConfig) {
      getSchema(dbConfig)
        .then((s: SchemaResponse) => setSchemaContext(s as Record<string, unknown>))
        .catch(() => setSchemaContext(null));
    } else {
      setSchemaContext(null);
    }
  }, [isConnected, dbConfig]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    setLoading(true);
    setError(null);
    try {
      const res = await chat(text, {
        includeSql: true,
        schemaContext: schemaContext ?? undefined,
      });
      const reply = [res.message, res.explanation].filter(Boolean).join("\n\n") || "No response.";
      const sql = typeof res.sql === "string" ? res.sql : undefined;
      setMessages((m) => [...m, { role: "assistant", content: reply, sql }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
      setMessages((m) => [...m, { role: "assistant", content: `Error: ${err instanceof Error ? err.message : "Request failed"}` }]);
    } finally {
      setLoading(false);
    }
  };

  if (!isConnected || !dbConfig) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 dark:border-amber-800 dark:bg-amber-900/20">
        <p className="text-amber-800 dark:text-amber-200">
          Connect a database on the <Link href="/" className="underline hover:no-underline">Home</Link> page first.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">AI Chatbot</h1>
      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
          {error}
        </div>
      )}

      <div className="max-h-[60vh] space-y-4 overflow-y-auto rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
        {messages.length === 0 && (
          <p className="text-slate-500 dark:text-slate-400">Ask a question about your data or ask for SQL.</p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`rounded-lg p-3 ${
              msg.role === "user"
                ? "ml-8 bg-indigo-100 dark:bg-indigo-900/30"
                : "mr-8 bg-slate-100 dark:bg-slate-700"
            }`}
          >
            <div className="whitespace-pre-wrap text-slate-800 dark:text-slate-100">{msg.content}</div>
            {msg.sql && (
              <pre className="mt-2 overflow-x-auto rounded bg-slate-200 p-2 text-sm dark:bg-slate-600">
                {msg.sql}
              </pre>
            )}
          </div>
        ))}
        {loading && (
          <div className="mr-8 rounded-lg bg-slate-100 p-3 dark:bg-slate-700">
            <span className="text-slate-500">Thinking…</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question or request SQL..."
          className="flex-1 rounded-lg border border-slate-300 px-4 py-2 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
