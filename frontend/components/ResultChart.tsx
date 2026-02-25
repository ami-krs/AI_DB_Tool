"use client";

import { useMemo, useState } from "react";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

function isNumericLike(value: unknown): boolean {
  if (value == null) return false;
  if (typeof value === "number" && !Number.isNaN(value)) return true;
  const s = String(value).trim();
  if (!s) return false;
  return !Number.isNaN(Number(s));
}

type ResultChartProps = {
  columns: string[];
  rows: Record<string, unknown>[];
  defaultChartType?: "bar" | "line";
};

export function ResultChart({ columns, rows, defaultChartType = "bar" }: ResultChartProps) {
  const [chartType, setChartType] = useState<"bar" | "line">(defaultChartType);
  const [xCol, setXCol] = useState<string>("");
  const [yCol, setYCol] = useState<string>("");

  const { numericCols, categoricalCols, data } = useMemo(() => {
    if (!columns.length || !rows.length) {
      return { numericCols: [], categoricalCols: [], data: [] };
    }
    const numericCols: string[] = [];
    const categoricalCols: string[] = [];
    for (const col of columns) {
      const sample = rows.slice(0, Math.min(20, rows.length)).map((r) => r[col]);
      const numericCount = sample.filter(isNumericLike).length;
      if (numericCount >= sample.length / 2) numericCols.push(col);
      else categoricalCols.push(col);
    }
    const data = rows.slice(0, 100).map((row, i) => {
      const point: Record<string, unknown> = { __index: i };
      columns.forEach((c) => (point[c] = row[c]));
      return point;
    });
    return { numericCols, categoricalCols, data };
  }, [columns, rows]);

  const xCols = categoricalCols.length ? categoricalCols : columns.slice(0, 1);
  const yCols = numericCols.length ? numericCols : columns.slice(0, 2);
  const currentX = xCol || xCols[0];
  const currentY = yCol || yCols[0];

  if (!columns.length || !rows.length || !currentX || !currentY) {
    return (
      <p className="text-sm text-slate-500 dark:text-slate-400">Not enough columns for a chart.</p>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <select
          value={chartType}
          onChange={(e) => setChartType(e.target.value as "bar" | "line")}
          className="rounded border border-slate-300 bg-white px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
        >
          <option value="bar">Bar</option>
          <option value="line">Line</option>
        </select>
        <label className="text-sm text-slate-600 dark:text-slate-400">
          X:{" "}
          <select
            value={currentX}
            onChange={(e) => setXCol(e.target.value)}
            className="rounded border border-slate-300 bg-white px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
          >
            {columns.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </label>
        <label className="text-sm text-slate-600 dark:text-slate-400">
          Y:{" "}
          <select
            value={currentY}
            onChange={(e) => setYCol(e.target.value)}
            className="rounded border border-slate-300 bg-white px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
          >
            {columns.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </label>
      </div>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === "bar" ? (
            <BarChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={currentX} tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey={currentY} fill="#6366f1" name={currentY} />
            </BarChart>
          ) : (
            <LineChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={currentX} tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Line type="monotone" dataKey={currentY} stroke="#6366f1" name={currentY} />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
