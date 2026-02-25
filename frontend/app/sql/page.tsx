"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import Link from "next/link";
import Editor from "react-simple-code-editor";
import Prism from "prismjs";
import "prismjs/components/prism-sql";
import { useDbConfig } from "@/lib/db-config";
import { executeQuery, getSchema, debugError } from "@/lib/api";
import type { DebugErrorResult } from "@/lib/api";
import type { QueryResult, SchemaResponse } from "@/lib/types";
import { downloadResultCsv } from "@/lib/csv";
import { ResultChart } from "@/components/ResultChart";

function highlightSql(code: string) {
  return Prism.highlight(code, Prism.languages.sql, "sql");
}

const SQL_KEYWORDS = [
  "SELECT",
  "FROM",
  "WHERE",
  "GROUP BY",
  "ORDER BY",
  "LIMIT",
  "JOIN",
  "LEFT JOIN",
  "RIGHT JOIN",
  "INNER JOIN",
  "INSERT INTO",
  "UPDATE",
  "DELETE",
  "CREATE TABLE",
  "ALTER TABLE",
  "DROP TABLE",
  "AND",
  "OR",
  "AS",
  "ON",
  "ASC",
  "DESC",
  "IN",
  "NOT NULL",
  "VALUES",
  "SET",
];

function getSuggestions(
  textBeforeCursor: string,
  tables: string[]
): { label: string; insertText: string; kind: "keyword" | "table" }[] {
  const suggestions: { label: string; insertText: string; kind: "keyword" | "table" }[] = [];

  // After "FROM " or "SELECT * FROM " → suggest tables
  if (/\bFROM\s+$/i.test(textBeforeCursor)) {
    tables.forEach((t) => {
      suggestions.push({ label: t, insertText: t, kind: "table" });
    });
    return suggestions;
  }

  const tokenMatch = textBeforeCursor.match(/([A-Za-z_][A-Za-z0-9_]*)$/);
  const token = tokenMatch ? tokenMatch[1] : "";
  if (!token) return suggestions;

  const upperToken = token.toUpperCase();

  SQL_KEYWORDS.forEach((kw) => {
    if (kw.indexOf(upperToken) === 0) {
      suggestions.push({ label: kw, insertText: kw, kind: "keyword" });
    }
  });

  tables.forEach((tableName) => {
    if (tableName.toUpperCase().indexOf(upperToken) === 0) {
      suggestions.push({ label: tableName, insertText: tableName, kind: "table" });
    }
  });

  return suggestions;
}

export default function SqlPage() {
  const { dbConfig, isConnected } = useDbConfig();
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [debugHint, setDebugHint] = useState<DebugErrorResult | null>(null);
  const [debugLoading, setDebugLoading] = useState(false);
  const [showChart, setShowChart] = useState(false);
  const [tables, setTables] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<{ label: string; insertText: string; kind: "keyword" | "table" }[]>([]);
  const [suggestionIndex, setSuggestionIndex] = useState(0);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [copyFeedback, setCopyFeedback] = useState(false);
  const editorContainerRef = useRef<HTMLDivElement>(null);
  const cursorRef = useRef(0);
  const insertCursorRef = useRef<number | null>(null);

  const copyToClipboard = (text: string) => {
    if (!text.trim()) return;
    void navigator.clipboard.writeText(text).then(() => {
      setCopyFeedback(true);
      setTimeout(() => setCopyFeedback(false), 2000);
    });
  };

  const getTextarea = () =>
    editorContainerRef.current?.querySelector("textarea") as HTMLTextAreaElement | null;

  useEffect(() => {
    if (!dbConfig || !isConnected) return;
    getSchema(dbConfig)
      .then((s: SchemaResponse) => {
        const names = (s.tables ?? []).map((t) => t.table_name);
        setTables(names);
      })
      .catch(() => setTables([]));
  }, [dbConfig, isConnected]);

  useEffect(() => {
    const el = getTextarea();
    if (el && insertCursorRef.current != null) {
      const pos = insertCursorRef.current;
      insertCursorRef.current = null;
      el.focus();
      el.setSelectionRange(pos, pos);
    }
  }, [query]);

  const handleRun = useCallback(async () => {
    if (!dbConfig || !query.trim() || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setDebugHint(null);
    setShowSuggestions(false);
    try {
      const res = await executeQuery(dbConfig, query);
      setResult(res);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : "Execution failed";
      setError(errMsg);
      setDebugLoading(true);
      try {
        const hint = await debugError(dbConfig, query, errMsg);
        setDebugHint(hint);
      } catch {
        setDebugHint(null);
      } finally {
        setDebugLoading(false);
      }
    } finally {
      setLoading(false);
    }
  }, [dbConfig, query, loading]);

  const handleEditorChange = (code: string) => {
    setQuery(code);
    const ta = getTextarea();
    const pos = ta ? ta.selectionStart : code.length;
    cursorRef.current = pos;
    const before = code.slice(0, pos);
    const next = getSuggestions(before, tables);
    setSuggestions(next);
    setShowSuggestions(next.length > 0);
    setSuggestionIndex(0);
  };

  const insertSuggestion = (suggestion: { insertText: string }) => {
    const pos = cursorRef.current;
    const value = query;
    const before = value.slice(0, pos);
    const tokenMatch = before.match(/([A-Za-z_][A-Za-z0-9_]*)$/);
    let wordStart: number;
    let wordEnd: number;
    if (/\bFROM\s+$/i.test(before)) {
      wordStart = pos;
      wordEnd = pos;
    } else if (tokenMatch) {
      wordEnd = pos;
      wordStart = pos - tokenMatch[1].length;
    } else {
      return;
    }
    const newQuery = value.slice(0, wordStart) + suggestion.insertText + value.slice(wordEnd);
    insertCursorRef.current = wordStart + suggestion.insertText.length;
    setQuery(newQuery);
    setShowSuggestions(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    const ta = getTextarea();
    if (ta) cursorRef.current = ta.selectionStart;
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      handleRun();
      return;
    }
    if (!showSuggestions || suggestions.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSuggestionIndex((i) => (i + 1) % suggestions.length);
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      setSuggestionIndex((i) => (i - 1 + suggestions.length) % suggestions.length);
      return;
    }
    if (e.key === "Enter" || e.key === "Tab") {
      e.preventDefault();
      insertSuggestion(suggestions[suggestionIndex]);
      return;
    }
    if (e.key === "Escape") {
      e.preventDefault();
      setShowSuggestions(false);
    }
  };

  const handleBlur = () => {
    if (showSuggestions) {
      setTimeout(() => setShowSuggestions(false), 150);
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
    <div className="mx-auto max-w-6xl space-y-4">
      <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">SQL Editor</h1>
      <p className="text-sm text-slate-600 dark:text-slate-400">
        Type SQL with hints (e.g. <kbd className="rounded bg-slate-200 px-1 dark:bg-slate-600">SEL</kbd> → SELECT, after <kbd className="rounded bg-slate-200 px-1 dark:bg-slate-600">FROM </kbd> choose a table). Use <kbd className="rounded bg-slate-200 px-1 dark:bg-slate-600">⌘+Enter</kbd> (Mac) or <kbd className="rounded bg-slate-200 px-1 dark:bg-slate-600">Ctrl+Enter</kbd> to execute.
      </p>
      {error && (
        <div className="space-y-3">
          <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
            {error}
          </div>
          {debugLoading && (
            <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300">
              <span className="animate-pulse">🐛</span>
              Debugging with AI…
            </div>
          )}
          {debugHint && !debugLoading && (
            <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-600 dark:bg-slate-800">
              <div className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                <span>🐛</span>
                {debugHint.agent_name}
                {debugHint.confidence > 0 && (
                  <span className="text-slate-500 dark:text-slate-400">
                    (confidence {(debugHint.confidence * 100).toFixed(0)}%)
                  </span>
                )}
              </div>
              {debugHint.analysis && (
                <div className="prose prose-sm max-w-none rounded-lg bg-slate-50 p-3 text-slate-700 dark:prose-invert dark:bg-slate-900 dark:text-slate-300">
                  <p className="whitespace-pre-wrap text-sm">{debugHint.analysis}</p>
                </div>
              )}
              {debugHint.suggestions && debugHint.suggestions.length > 0 && (
                <ul className="mt-2 list-inside list-decimal space-y-0.5 text-sm text-slate-600 dark:text-slate-400">
                  {debugHint.suggestions.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              )}
              {debugHint.suggested_sql && (
                <div className="mt-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        setQuery(debugHint!.suggested_sql!);
                        setError(null);
                        setDebugHint(null);
                      }}
                      className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700"
                    >
                      Use suggested SQL
                    </button>
                    <button
                      type="button"
                      onClick={() => copyToClipboard(debugHint.suggested_sql!)}
                      title="Copy suggested SQL"
                      className="flex h-8 w-8 items-center justify-center rounded border border-slate-200 bg-white text-slate-500 hover:bg-slate-50 hover:text-slate-700 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-400 dark:hover:bg-slate-600 dark:hover:text-slate-200"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                      </svg>
                    </button>
                  </div>
                  <pre className="mt-2 max-h-40 overflow-auto rounded border border-slate-200 bg-slate-50 p-2 font-mono text-xs dark:border-slate-600 dark:bg-slate-900">
                    <code>{debugHint.suggested_sql}</code>
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      <div className="relative group">
        <button
          type="button"
          onClick={() => copyToClipboard(query)}
          title="Copy SQL"
          className="absolute right-2 top-2 z-10 flex h-8 w-8 items-center justify-center rounded border border-slate-200 bg-white/90 text-slate-500 opacity-0 shadow-sm transition-opacity hover:bg-slate-50 hover:text-slate-700 group-hover:opacity-100 dark:border-slate-600 dark:bg-slate-800/90 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-slate-200"
        >
          {copyFeedback ? (
            <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">Copied!</span>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
            </svg>
          )}
        </button>
        <div
          ref={editorContainerRef}
          className="sql-editor-wrapper w-full overflow-hidden rounded-lg border border-slate-300 bg-white p-3 text-slate-700 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
        >
          <Editor
            value={query}
            onValueChange={handleEditorChange}
            highlight={highlightSql}
            onKeyDown={handleKeyDown}
            onBlur={handleBlur}
            onClick={() => {
              setTimeout(() => {
                const ta = getTextarea();
                if (ta) cursorRef.current = ta.selectionStart;
              }, 0);
            }}
            placeholder="SELECT * FROM ..."
            padding={0}
            style={{
              fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
              fontSize: 14,
              minHeight: 200,
            }}
            textareaClassName="sql-editor-textarea"
            preClassName="sql-editor-pre min-h-[200px] [&_.token.keyword]:!text-blue-600 [&_.token.keyword]:dark:!text-blue-400 [&_.token.builtin]:!text-blue-600 [&_.token.builtin]:dark:!text-blue-400 [&_.token.boolean]:!text-blue-600 [&_.token.boolean]:dark:!text-blue-400 [&_.token.function]:!text-violet-600 [&_.token.function]:dark:!text-violet-400 [&_.token.string]:!text-emerald-600 [&_.token.string]:dark:!text-emerald-400 [&_.token.number]:!text-amber-600 [&_.token.number]:dark:!text-amber-400 [&_.token.comment]:!text-slate-500 [&_.token.comment]:dark:!text-slate-400 [&_.token.comment]:italic"
          />
        </div>
        {showSuggestions && suggestions.length > 0 && (
          <ul
            className="absolute z-10 mt-0.5 max-h-48 w-full overflow-auto rounded-lg border border-slate-200 bg-white py-1 shadow-lg dark:border-slate-600 dark:bg-slate-800"
            style={{ top: "100%" }}
          >
            {suggestions.map((s, i) => (
              <li key={`${s.kind}-${s.label}-${i}`}>
                <button
                  type="button"
                  onMouseDown={(e) => {
                    e.preventDefault();
                    insertSuggestion(s);
                  }}
                  className={`flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm font-mono ${
                    i === suggestionIndex
                      ? "bg-indigo-100 text-indigo-900 dark:bg-indigo-900/50 dark:text-indigo-100"
                      : "text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-700"
                  }`}
                >
                  <span className="text-slate-400 dark:text-slate-500">
                    {s.kind === "table" ? "📋" : "⌨"}
                  </span>
                  {s.label}
                </button>
              </li>
            ))}
          </ul>
        )}
        <button
          onClick={() => handleRun()}
          disabled={loading || !query.trim()}
          className="mt-2 rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "Running…" : "Execute"}
        </button>
      </div>

      {result && (
        <div className="rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 p-3 dark:border-slate-700">
            <span className="text-sm text-slate-600 dark:text-slate-400">
              {result.kind === "result_set"
                ? `${result.row_count ?? 0} row(s)`
                : `Affected rows: ${result.affected_rows ?? 0}`}
            </span>
            {result.kind === "result_set" && result.columns && result.rows && (
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() =>
                    downloadResultCsv(result.columns!, result.rows!, "sql_result.csv")
                  }
                  className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
                >
                  Download CSV
                </button>
                <button
                  type="button"
                  onClick={() => setShowChart((v) => !v)}
                  className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
                >
                  {showChart ? "Hide chart" : "Chart"}
                </button>
              </div>
            )}
          </div>
          {result.kind === "result_set" && result.columns && result.rows && (
            <>
              <div className="overflow-x-auto p-2">
                <table className="min-w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 dark:border-slate-600">
                      {result.columns.map((col) => (
                        <th key={col} className="px-3 py-2 font-medium text-slate-700 dark:text-slate-300">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.rows.map((row, i) => (
                      <tr key={i} className="border-b border-slate-100 dark:border-slate-700">
                        {result.columns!.map((col) => (
                          <td key={col} className="px-3 py-2 text-slate-600 dark:text-slate-400">
                            {String(row[col] ?? "")}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {showChart && (
                <div className="border-t border-slate-200 p-3 dark:border-slate-700">
                  <ResultChart columns={result.columns} rows={result.rows} />
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
