"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import Link from "next/link";
import { useDbConfig } from "@/lib/db-config";
import { chat, getSchema, executeQuery, importSmart, type SmartImportResult } from "@/lib/api";
import type { SchemaResponse } from "@/lib/types";
import type { QueryResult } from "@/lib/types";
import { downloadResultCsv } from "@/lib/csv";
import { ResultChart } from "@/components/ResultChart";
import { parseCsv } from "@/lib/csv-parse";

const CHAT_HISTORY_KEY = "chat_history";
const MAX_SAVED_MESSAGES = 500;

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  sql?: string;
  executionResult?: QueryResult;
  executionError?: string;
  showUploadPanel?: boolean;
  uploadTargetTable?: string;
  createdAt?: string;
};

function getDateKey(iso: string): string {
  try {
    return new Date(iso).toISOString().slice(0, 10);
  } catch {
    return new Date().toISOString().slice(0, 10);
  }
}

function getDateLabel(dateKey: string): string {
  const today = new Date().toISOString().slice(0, 10);
  if (dateKey === today) return "Today";
  const yesterday = new Date(Date.now() - 864e5).toISOString().slice(0, 10);
  if (dateKey === yesterday) return "Yesterday";
  try {
    const [y, m, d] = dateKey.split("-").map(Number);
    const date = new Date(y, m - 1, d);
    return date.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric", year: "numeric" });
  } catch {
    return dateKey;
  }
}

function groupMessagesByDate(messages: ChatMessage[]): { dateKey: string; dateLabel: string; messages: ChatMessage[] }[] {
  const withDate = messages.map((m, i) => ({
    msg: m,
    dateKey: m.createdAt ? getDateKey(m.createdAt) : new Date().toISOString().slice(0, 10),
    order: i,
  }));
  const byDate = new Map<string, { dateKey: string; messages: ChatMessage[]; order: number }>();
  withDate.forEach(({ msg, dateKey, order }) => {
    if (!byDate.has(dateKey)) byDate.set(dateKey, { dateKey, messages: [], order: Number.MAX_SAFE_INTEGER });
    const g = byDate.get(dateKey)!;
    g.messages.push(msg);
    g.order = Math.min(g.order, order);
  });
  return Array.from(byDate.values())
    .sort((a, b) => a.order - b.order)
    .map((g) => ({ dateKey: g.dateKey, dateLabel: getDateLabel(g.dateKey), messages: g.messages }));
}

function isSelectLike(sql: string): boolean {
  const t = sql.trim().toUpperCase();
  return t.startsWith("SELECT") || t.startsWith("WITH") || t.startsWith("SHOW") || t.startsWith("DESCRIBE") || t.startsWith("EXPLAIN");
}

function loadChatHistory(): ChatMessage[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(CHAT_HISTORY_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    const now = new Date().toISOString();
    return parsed.slice(-MAX_SAVED_MESSAGES).map((m: Record<string, unknown>) => ({
      ...m,
      createdAt: (m.createdAt as string) || now,
    })) as ChatMessage[];
  } catch {
    return [];
  }
}

function saveChatHistory(messages: ChatMessage[]) {
  if (typeof window === "undefined" || messages.length === 0) return;
  try {
    const toSave = messages.slice(-MAX_SAVED_MESSAGES);
    localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(toSave));
  } catch {
    // ignore quota or parse errors
  }
}

export default function ChatPage() {
  const { dbConfig, isConnected } = useDbConfig();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [schemaContext, setSchemaContext] = useState<Record<string, unknown> | null>(null);
  const [autoExecuteSelect, setAutoExecuteSelect] = useState(true);
  const [executingIndex, setExecutingIndex] = useState<number | null>(null);
  const [showChartIndex, setShowChartIndex] = useState<number | null>(null);
  const [uploadTable, setUploadTable] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadResult, setUploadResult] = useState<SmartImportResult | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [activeUploadMessageIndex, setActiveUploadMessageIndex] = useState<number | null>(null);
  const [copySqlIndex, setCopySqlIndex] = useState<number | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const copySqlToClipboard = (sql: string, index: number) => {
    if (!sql.trim()) return;
    void navigator.clipboard.writeText(sql).then(() => {
      setCopySqlIndex(index);
      setTimeout(() => setCopySqlIndex(null), 2000);
    });
  };

  const tableNames = (schemaContext?.tables as { table_name: string }[] | undefined)?.map((t) => t.table_name) ?? [];

  useEffect(() => {
    if (!historyLoaded) {
      setMessages(loadChatHistory());
      setHistoryLoaded(true);
    }
  }, [historyLoaded]);

  useEffect(() => {
    if (historyLoaded && messages.length > 0) saveChatHistory(messages);
  }, [historyLoaded, messages]);

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

  const messageGroups = useMemo(() => groupMessagesByDate(messages), [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    const userMsg: ChatMessage = { role: "user", content: text, createdAt: new Date().toISOString() };
    setMessages((m) => [...m, userMsg]);
    setLoading(true);
    setError(null);
    try {
      const res = await chat(text, {
        includeSql: true,
        schemaContext: schemaContext ?? undefined,
      });
      // Backend returns { response, sql_query, error } (not message/explanation/sql)
      const reply =
        res.error ||
        (typeof res.response === "string" ? res.response.trim() : "") ||
        "No response.";
      const sql =
        typeof res.sql_query === "string" ? res.sql_query.trim() || undefined : undefined;
      const newMsg: ChatMessage = {
        role: "assistant",
        content: reply,
        sql,
        showUploadPanel: !!res.show_upload_panel,
        uploadTargetTable: typeof res.upload_target_table === "string" ? res.upload_target_table : undefined,
        createdAt: new Date().toISOString(),
      };
      setMessages((m) => {
        const next = [...m, newMsg];
        const newIndex = next.length - 1;
        // Auto-execute SELECT-like queries when option is on
        if (sql && autoExecuteSelect && isSelectLike(sql) && dbConfig) {
          executeQuery(dbConfig, sql)
            .then((result) => {
              setMessages((prev) => {
                const copy = [...prev];
                if (copy[newIndex]?.role === "assistant") {
                  copy[newIndex] = { ...copy[newIndex], executionResult: result };
                }
                return copy;
              });
            })
            .catch((err) => {
              setMessages((prev) => {
                const copy = [...prev];
                if (copy[newIndex]?.role === "assistant") {
                  copy[newIndex] = { ...copy[newIndex], executionError: err instanceof Error ? err.message : String(err) };
                }
                return copy;
              });
            });
        }
        return next;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `Error: ${err instanceof Error ? err.message : "Request failed"}`, createdAt: new Date().toISOString() },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async (index: number) => {
    const msg = messages[index];
    if (!msg?.sql || !dbConfig) return;
    setExecutingIndex(index);
    setMessages((prev) => {
      const copy = [...prev];
      if (copy[index]) {
        copy[index] = { ...copy[index], executionError: undefined, executionResult: undefined };
      }
      return copy;
    });
    try {
      const result = await executeQuery(dbConfig, msg.sql);
      setMessages((prev) => {
        const copy = [...prev];
        if (copy[index]) copy[index] = { ...copy[index], executionResult: result };
        return copy;
      });
    } catch (err) {
      setMessages((prev) => {
        const copy = [...prev];
        if (copy[index]) {
          copy[index] = { ...copy[index], executionError: err instanceof Error ? err.message : String(err) };
        }
        return copy;
      });
    } finally {
      setExecutingIndex(null);
    }
  };

  const handleLoadFile = async (messageIndex: number) => {
    if (!dbConfig || !uploadFile) return;
    const msg = messages[messageIndex];
    const table = (uploadTable || msg?.uploadTargetTable || tableNames[0] || "").trim();
    if (!table) return;
    setActiveUploadMessageIndex(messageIndex);
    setUploadLoading(true);
    setUploadError(null);
    setUploadResult(null);
    const reader = new FileReader();
    reader.onload = async () => {
      try {
        const text = String(reader.result ?? "");
        const { headers, rows } = parseCsv(text);
        const rowsAsObjects = rows.map((row) => {
          const obj: Record<string, unknown> = {};
          headers.forEach((h, j) => (obj[h] = row[j]));
          return obj;
        });
        const result = await importSmart(dbConfig, table, rowsAsObjects);
        setUploadResult(result);
      } catch (e) {
        setUploadError(e instanceof Error ? e.message : String(e));
      } finally {
        setUploadLoading(false);
      }
    };
    reader.readAsText(uploadFile);
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
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">AI Chatbot</h1>
        <div className="flex flex-wrap items-center gap-4">
          {messages.length > 0 && (
            <button
              type="button"
              onClick={() => {
                if (typeof window !== "undefined" && window.confirm("Clear all chat history?")) {
                  setMessages([]);
                  localStorage.removeItem(CHAT_HISTORY_KEY);
                }
              }}
              className="text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
            >
              Clear history
            </button>
          )}
          <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
            <input
              type="checkbox"
              checked={autoExecuteSelect}
              onChange={(e) => setAutoExecuteSelect(e.target.checked)}
              className="rounded border-slate-300"
            />
            Auto-run SELECT queries
          </label>
        </div>
      </div>
      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
          {error}
        </div>
      )}

      <div className="max-h-[60vh] space-y-4 overflow-y-auto rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
        {messages.length === 0 && (
          <p className="text-slate-500 dark:text-slate-400">Ask a question about your data or ask for SQL.</p>
        )}
        {messageGroups.map((group) => {
          const startIdx = messages.indexOf(group.messages[0]);
          return (
            <div key={group.dateKey} className="space-y-2">
              <div className="sticky top-0 z-10 border-b border-slate-200 bg-white py-1.5 text-xs font-medium text-slate-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-400">
                {group.dateLabel}
              </div>
              {group.messages.map((msg, j) => {
                const i = startIdx + j;
                return (
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
              <div className="mt-2 group/sql">
                <div className="relative">
                  <pre className="overflow-x-auto rounded bg-slate-200 p-2 pr-10 text-sm dark:bg-slate-600">
                    {msg.sql}
                  </pre>
                  <button
                    type="button"
                    onClick={() => copySqlToClipboard(msg.sql!, i)}
                    title="Copy SQL"
                    className="absolute right-1 top-1 flex h-7 w-7 items-center justify-center rounded border border-slate-300 bg-white/90 text-slate-500 opacity-0 transition-opacity hover:bg-slate-100 hover:text-slate-700 group-hover/sql:opacity-100 dark:border-slate-500 dark:bg-slate-700/90 dark:text-slate-400 dark:hover:bg-slate-600 dark:hover:text-slate-200"
                  >
                    {copySqlIndex === i ? (
                      <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">Copied!</span>
                    ) : (
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                      </svg>
                    )}
                  </button>
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => handleExecute(i)}
                    disabled={executingIndex === i}
                    className="rounded bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                  >
                    {executingIndex === i ? "Running…" : "Execute SQL"}
                  </button>
                  {msg.executionResult?.kind === "result_set" && msg.executionResult.columns && msg.executionResult.rows && (
                    <>
                      <button
                        type="button"
                        onClick={() =>
                          downloadResultCsv(
                            msg.executionResult!.columns!,
                            msg.executionResult!.rows!,
                            `chat_result_${i}.csv`
                          )
                        }
                        className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
                      >
                        Download CSV
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowChartIndex(showChartIndex === i ? null : i)}
                        className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
                      >
                        {showChartIndex === i ? "Hide chart" : "Chart"}
                      </button>
                    </>
                  )}
                </div>
                {msg.executionError && (
                  <div className="mt-2 rounded bg-red-100 p-2 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-300">
                    {msg.executionError}
                  </div>
                )}
                {msg.executionResult && (
                  <div className="mt-2 rounded border border-slate-200 bg-white dark:border-slate-600 dark:bg-slate-800">
                    {msg.executionResult.kind === "result_set" && msg.executionResult.columns && msg.executionResult.rows && (
                      <div className="overflow-x-auto p-2">
                        <table className="min-w-full text-left text-sm">
                          <thead>
                            <tr className="border-b border-slate-200 dark:border-slate-600">
                              {msg.executionResult.columns.map((col) => (
                                <th key={col} className="px-2 py-1 font-medium text-slate-700 dark:text-slate-300">{col}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {msg.executionResult.rows.map((row, ri) => (
                              <tr key={ri} className="border-b border-slate-100 dark:border-slate-700">
                                {msg.executionResult!.columns!.map((col) => (
                                  <td key={col} className="px-2 py-1 text-slate-600 dark:text-slate-400">{String(row[col] ?? "")}</td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        <p className="mt-1 text-xs text-slate-500">{msg.executionResult.row_count ?? 0} row(s)</p>
                      </div>
                    )}
                    {msg.executionResult.kind === "non_query" && (
                      <p className="p-2 text-sm text-slate-600 dark:text-slate-400">
                        Affected rows: {msg.executionResult.affected_rows ?? 0}
                      </p>
                    )}
                  </div>
                )}
                {showChartIndex === i && msg.executionResult?.kind === "result_set" && msg.executionResult.columns && msg.executionResult.rows && (
                  <div className="mt-2 rounded border border-slate-200 bg-white p-2 dark:border-slate-600 dark:bg-slate-800">
                    <ResultChart
                      columns={msg.executionResult.columns}
                      rows={msg.executionResult.rows}
                    />
                  </div>
                )}
              </div>
            )}
            {msg.showUploadPanel && (
              <div className="mt-3 rounded border border-slate-300 bg-white p-3 dark:border-slate-600 dark:bg-slate-800">
                <p className="mb-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                  Upload local file to database table
                </p>
                <p className="mb-2 text-xs text-slate-500 dark:text-slate-400">
                  Column names are matched case-insensitively. Primary key duplicates are auto-handled.
                </p>
                <div className="flex flex-wrap items-end gap-3">
                  <div>
                    <label className="mb-1 block text-xs text-slate-600 dark:text-slate-400">Target table</label>
                    <select
                      value={uploadTable || msg.uploadTargetTable || tableNames[0] || ""}
                      onChange={(e) => setUploadTable(e.target.value)}
                      className="rounded border border-slate-300 bg-white px-2 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
                    >
                      {tableNames.map((t) => (
                        <option key={t} value={t}>{t}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-xs text-slate-600 dark:text-slate-400">CSV file</label>
                    <input
                      type="file"
                      accept=".csv,text/csv,.tsv,.txt"
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        setUploadFile(f || null);
                        setActiveUploadMessageIndex(i);
                      }}
                      className="block text-sm text-slate-600 dark:text-slate-400"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => handleLoadFile(i)}
                    disabled={uploadLoading || !uploadFile}
                    className="rounded bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                  >
                    {uploadLoading ? "Loading…" : "Load file to table"}
                  </button>
                </div>
                {activeUploadMessageIndex === i && uploadResult && (
                  <div className="mt-2 rounded bg-green-50 p-2 text-sm text-green-800 dark:bg-green-900/20 dark:text-green-300">
                    Loaded {uploadResult.inserted} row(s) into {uploadResult.table}.
                    {uploadResult.hint && <span className="block mt-1 text-xs">{uploadResult.hint}</span>}
                  </div>
                )}
                {activeUploadMessageIndex === i && uploadError && (
                  <div className="mt-2 rounded bg-red-50 p-2 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
                    {uploadError}
                  </div>
                )}
              </div>
            )}
                  </div>
                );
              })}
            </div>
          );
        })}
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
