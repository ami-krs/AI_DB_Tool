import type { DbConfig, ChatResponse, QueryResult, SchemaResponse } from "./types";

const getBaseUrl = (): string => {
  if (typeof window !== "undefined") {
    return (process.env.NEXT_PUBLIC_BACKEND_API_URL || "").trim() || "http://localhost:8000";
  }
  return process.env.NEXT_PUBLIC_BACKEND_API_URL || "http://localhost:8000";
};

const getToken = (): string => {
  if (typeof window !== "undefined") {
    return (process.env.NEXT_PUBLIC_BACKEND_API_TOKEN || "").trim();
  }
  return "";
};

function headers(): HeadersInit {
  const h: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const token = getToken();
  if (token) h["X-API-Token"] = token;
  return h;
}

export async function healthCheck(): Promise<{ status: string }> {
  const res = await fetch(`${getBaseUrl().replace(/\/$/, "")}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function chat(
  userMessage: string,
  options: { includeSql?: boolean; schemaContext?: Record<string, unknown> } = {}
): Promise<ChatResponse> {
  const res = await fetch(`${getBaseUrl().replace(/\/$/, "")}/v1/chat`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({
      user_message: userMessage,
      include_sql: options.includeSql ?? true,
      schema_context: options.schemaContext ?? null,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || res.statusText);
  }
  return res.json();
}

export async function executeQuery(dbConfig: DbConfig, query: string): Promise<QueryResult> {
  const res = await fetch(`${getBaseUrl().replace(/\/$/, "")}/v1/query/execute`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ db_config: dbConfig, query: query.trim() }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || res.statusText);
  }
  return res.json();
}

export async function getSchema(dbConfig: DbConfig): Promise<SchemaResponse> {
  const res = await fetch(`${getBaseUrl().replace(/\/$/, "")}/v1/schema`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ db_config: dbConfig }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || res.statusText);
  }
  return res.json();
}
