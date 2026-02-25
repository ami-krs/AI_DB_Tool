/**
 * Build CSV string from columns and rows, then trigger browser download.
 */
export function downloadResultCsv(
  columns: string[],
  rows: Record<string, unknown>[],
  filename: string = "query_result.csv"
): void {
  const header = columns.map((c) => (c.includes(",") || c.includes('"') ? `"${c.replace(/"/g, '""')}"` : c)).join(",");
  const body = rows
    .map((row) =>
      columns
        .map((col) => {
          const v = row[col];
          const s = v == null ? "" : String(v);
          return s.includes(",") || s.includes('"') || s.includes("\n") ? `"${s.replace(/"/g, '""')}"` : s;
        })
        .join(",")
    )
    .join("\n");
  const csv = header + "\n" + body;
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
