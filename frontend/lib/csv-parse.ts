/**
 * Parse CSV string into { headers, rows }.
 * Handles quoted fields (e.g. "a,b", "c").
 */
export function parseCsv(csvText: string): { headers: string[]; rows: string[][] } {
  const lines = csvText.split(/\r?\n/).filter((line) => line.trim());
  if (lines.length === 0) return { headers: [], rows: [] };
  const headers = parseCsvLine(lines[0]);
  const rows = lines.slice(1).map((line) => parseCsvLine(line));
  return { headers, rows };
}

function parseCsvLine(line: string): string[] {
  const out: string[] = [];
  let i = 0;
  while (i < line.length) {
    const rest = line.slice(i);
    if (rest.startsWith('"')) {
      let end = 1;
      let value = "";
      while (end < rest.length) {
        if (rest[end] === '"' && rest[end + 1] !== '"') {
          out.push(value);
          end++;
          const nextComma = rest.slice(end).indexOf(",");
          i += end + (nextComma === -1 ? rest.length - end : nextComma + 1);
          break;
        }
        if (rest[end] === '"' && rest[end + 1] === '"') {
          value += '"';
          end += 2;
        } else {
          value += rest[end];
          end++;
        }
      }
      if (end >= rest.length) {
        out.push(value);
        break;
      }
      continue;
    }
    const comma = rest.indexOf(",");
    if (comma === -1) {
      out.push(rest.trim());
      break;
    }
    out.push(rest.slice(0, comma).trim());
    i += comma + 1;
  }
  return out;
}
