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

export type AuthUser = { email: string; name?: string | null };
export type AuthResponse = { user: AuthUser; token: string };

export async function register(
  email: string,
  password: string,
  name?: string
): Promise<AuthResponse> {
  const res = await fetch(`${getBaseUrl().replace(/\/$/, "")}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: email.trim(), password, name: name?.trim() || null }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Registration failed");
  }
  return res.json();
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${getBaseUrl().replace(/\/$/, "")}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: email.trim(), password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Login failed");
  }
  return res.json();
}

export async function authMe(token: string): Promise<AuthUser> {
  const res = await fetch(`${getBaseUrl().replace(/\/$/, "")}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Invalid or expired token");
  const data = await res.json();
  return { email: data.email, name: data.name };
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

export type DebugErrorResult = {
  analysis: string | null;
  suggestions: string[];
  confidence: number;
  suggested_sql: string | null;
  agent_name: string;
};

export async function debugError(
  dbConfig: DbConfig,
  query: string,
  errorMessage: string
): Promise<DebugErrorResult> {
  const res = await fetch(`${getBaseUrl().replace(/\/$/, "")}/v1/debug-error`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({
      db_config: dbConfig,
      query: query.trim(),
      error_message: errorMessage,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || res.statusText);
  }
  return res.json();
}

export async function importTable(
  dbConfig: DbConfig,
  tableName: string,
  rows: Record<string, unknown>[]
): Promise<{ inserted: number; table: string }> {
  const res = await fetch(`${getBaseUrl().replace(/\/$/, "")}/v1/import`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({
      db_config: dbConfig,
      table_name: tableName,
      rows,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || res.statusText);
  }
  return res.json();
}

export type SmartImportResult = {
  inserted: number;
  table: string;
  loaded_columns: string[];
  remapped_pk_count: number;
  remapped_pk_column: string | null;
  skipped_existing_pk_count: number;
  skipped_file_duplicate_pk_count: number;
  hint: string | null;
};

export async function importSmart(
  dbConfig: DbConfig,
  tableName: string,
  rows: Record<string, unknown>[]
): Promise<SmartImportResult> {
  const res = await fetch(`${getBaseUrl().replace(/\/$/, "")}/v1/import/smart`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({
      db_config: dbConfig,
      table_name: tableName,
      rows,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || res.statusText);
  }
  return res.json();
}
