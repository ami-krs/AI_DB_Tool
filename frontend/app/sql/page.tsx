"use client";

import { useState } from "react";
import Link from "next/link";
import { useDbConfig } from "@/lib/db-config";
import { executeQuery } from "@/lib/api";
import type { QueryResult } from "@/lib/types";

export default function SqlPage() {
  const { dbConfig, isConnected } = useDbConfig();
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    if (!dbConfig || !query.trim() || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await executeQuery(dbConfig, query);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Execution failed");
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
    <div className="mx-auto max-w-6xl space-y-4">
      <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">SQL Editor</h1>
      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
          {error}
        </div>
      )}

      <div>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="SELECT * FROM ..."
          rows={8}
          className="w-full rounded-lg border border-slate-300 bg-white p-3 font-mono text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        />
        <button
          onClick={handleRun}
          disabled={loading || !query.trim()}
          className="mt-2 rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "Running…" : "Execute"}
        </button>
      </div>

      {result && (
        <div className="rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800">
          <div className="border-b border-slate-200 p-3 dark:border-slate-700">
            {result.kind === "result_set" ? (
              <span className="text-sm text-slate-600 dark:text-slate-400">
                {result.row_count ?? 0} row(s)
              </span>
            ) : (
              <span className="text-sm text-slate-600 dark:text-slate-400">
                Affected rows: {result.affected_rows ?? 0}
              </span>
            )}
          </div>
          {result.kind === "result_set" && result.columns && result.rows && (
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
          )}
        </div>
      )}
    </div>
  );
}
