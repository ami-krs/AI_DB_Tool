"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useDbConfig } from "@/lib/db-config";
import { getSchema } from "@/lib/api";
import type { SchemaResponse } from "@/lib/types";

export default function ExplorerPage() {
  const { dbConfig, isConnected } = useDbConfig();
  const [schema, setSchema] = useState<SchemaResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isConnected || !dbConfig) {
      setSchema(null);
      return;
    }
    setLoading(true);
    setError(null);
    getSchema(dbConfig)
      .then(setSchema)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load schema"))
      .finally(() => setLoading(false));
  }, [isConnected, dbConfig]);

  if (!isConnected || !dbConfig) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 dark:border-amber-800 dark:bg-amber-900/20">
        <p className="text-amber-800 dark:text-amber-200">
          Connect a database on the <Link href="/" className="underline hover:no-underline">Home</Link> page first.
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="text-slate-600 dark:text-slate-400">Loading schema…</div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 p-3 text-red-700 dark:bg-red-900/20 dark:text-red-300">
        {error}
      </div>
    );
  }

  const tables = schema?.tables ?? [];

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Data Explorer</h1>
      <p className="text-slate-600 dark:text-slate-400">
        {tables.length} table(s)
      </p>

      <div className="space-y-4">
        {tables.map((table) => (
          <div
            key={table.table_name}
            className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800"
          >
            <h2 className="mb-2 font-semibold text-slate-800 dark:text-slate-100">
              {table.table_name}
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-600">
                    <th className="px-3 py-2 font-medium text-slate-700 dark:text-slate-300">Column</th>
                    <th className="px-3 py-2 font-medium text-slate-700 dark:text-slate-300">Type</th>
                  </tr>
                </thead>
                <tbody>
                  {(table.columns || []).map((col) => (
                    <tr key={col.name} className="border-b border-slate-100 dark:border-slate-700">
                      <td className="px-3 py-2 text-slate-600 dark:text-slate-400">{col.name}</td>
                      <td className="px-3 py-2 text-slate-500 dark:text-slate-500">{col.type ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>

      {tables.length === 0 && (
        <p className="text-slate-500 dark:text-slate-400">No tables found.</p>
      )}
    </div>
  );
}
