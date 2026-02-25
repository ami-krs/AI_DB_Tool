"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useDbConfig } from "@/lib/db-config";
import { getSchema, importTable } from "@/lib/api";
import type { SchemaResponse } from "@/lib/types";
import { parseCsv } from "@/lib/csv-parse";

export default function UploadPage() {
  const { dbConfig, isConnected } = useDbConfig();
  const [schema, setSchema] = useState<SchemaResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [schemaError, setSchemaError] = useState<string | null>(null);
  const [selectedTable, setSelectedTable] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [csvHeaders, setCsvHeaders] = useState<string[]>([]);
  const [csvRows, setCsvRows] = useState<string[][]>([]);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<{ inserted: number } | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  useEffect(() => {
    if (!isConnected || !dbConfig) {
      setSchema(null);
      return;
    }
    setLoading(true);
    setSchemaError(null);
    getSchema(dbConfig)
      .then(setSchema)
      .catch((e) => setSchemaError(e instanceof Error ? e.message : "Failed to load schema"))
      .finally(() => setLoading(false));
  }, [isConnected, dbConfig]);

  const tables = schema?.tables ?? [];
  const tableColumns = tables.find((t) => t.table_name === selectedTable)?.columns ?? [];
  const tableColumnNames = tableColumns.map((c) => c.name);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setImportResult(null);
    setImportError(null);
    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result ?? "");
      const { headers, rows } = parseCsv(text);
      setCsvHeaders(headers);
      setCsvRows(rows);
      setMapping({});
    };
    reader.readAsText(f);
  };

  const setMap = (csvCol: string, tableCol: string) => {
    setMapping((m) => ({ ...m, [csvCol]: tableCol }));
  };

  const mappedRows = (): Record<string, unknown>[] => {
    const mappedCols = csvHeaders.filter((h) => mapping[h] && mapping[h] !== "__skip__");
    if (mappedCols.length === 0) return [];
    return csvRows.map((row) => {
      const obj: Record<string, unknown> = {};
      csvHeaders.forEach((h, i) => {
        const tc = mapping[h];
        if (tc && tc !== "__skip__") obj[tc] = row[i] ?? "";
      });
      return obj;
    });
  };

  const handleImport = async () => {
    if (!dbConfig || !selectedTable) return;
    const rows = mappedRows();
    if (rows.length === 0) {
      setImportError("Map at least one CSV column to a table column.");
      return;
    }
    setImporting(true);
    setImportError(null);
    setImportResult(null);
    try {
      const res = await importTable(dbConfig, selectedTable, rows);
      setImportResult({ inserted: res.inserted });
    } catch (e) {
      setImportError(e instanceof Error ? e.message : "Import failed");
    } finally {
      setImporting(false);
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
    <div className="mx-auto max-w-4xl space-y-6">
      <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Import data from CSV</h1>
      <p className="text-slate-600 dark:text-slate-400">
        Select a table, upload a CSV file, map CSV columns to table columns, then import.
      </p>

      {loading && <p className="text-slate-500">Loading schema…</p>}
      {schemaError && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
          {schemaError}
        </div>
      )}

      <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
        <label className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300">
          Target table
        </label>
        <select
          value={selectedTable}
          onChange={(e) => setSelectedTable(e.target.value)}
          className="w-full max-w-md rounded border border-slate-300 bg-white px-3 py-2 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
        >
          <option value="">Select table</option>
          {tables.map((t) => (
            <option key={t.table_name} value={t.table_name}>
              {t.table_name}
            </option>
          ))}
        </select>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
        <label className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300">
          CSV file
        </label>
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={handleFileChange}
          className="block w-full max-w-md text-sm text-slate-600 file:mr-4 file:rounded file:border-0 file:bg-indigo-50 file:px-4 file:py-2 file:text-indigo-700 dark:text-slate-400 dark:file:bg-indigo-900/30 dark:file:text-indigo-300"
        />
        {file && (
          <p className="mt-2 text-sm text-slate-500">
            {file.name} — {csvRows.length} row(s), {csvHeaders.length} column(s)
          </p>
        )}
      </div>

      {csvHeaders.length > 0 && selectedTable && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
          <h2 className="mb-3 text-lg font-semibold text-slate-800 dark:text-slate-100">
            Map CSV columns to table columns
          </h2>
          <div className="space-y-2">
            {csvHeaders.map((h) => (
              <div key={h} className="flex flex-wrap items-center gap-2">
                <span className="min-w-[120px] text-sm font-medium text-slate-600 dark:text-slate-400">
                  {h}
                </span>
                <span className="text-slate-400">→</span>
                <select
                  value={mapping[h] ?? ""}
                  onChange={(e) => setMap(h, e.target.value)}
                  className="rounded border border-slate-300 bg-white px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
                >
                  <option value="">—</option>
                  <option value="__skip__">Skip</option>
                  {tableColumnNames.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
          <p className="mt-2 text-xs text-slate-500">
            Rows to import: {mappedRows().length}. Map at least one column, then click Import.
          </p>
        </div>
      )}

      {csvHeaders.length > 0 && selectedTable && mappedRows().length > 0 && (
        <div className="flex gap-2">
          <button
            onClick={handleImport}
            disabled={importing}
            className="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {importing ? "Importing…" : "Import"}
          </button>
        </div>
      )}

      {importResult && (
        <div className="rounded-lg bg-green-50 p-3 text-green-800 dark:bg-green-900/20 dark:text-green-300">
          Imported {importResult.inserted} row(s) into {selectedTable}.
        </div>
      )}
      {importError && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
          {importError}
        </div>
      )}
    </div>
  );
}
