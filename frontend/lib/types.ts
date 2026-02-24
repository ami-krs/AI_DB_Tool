/** DB config sent to backend (matches backend DBConfigPayload). */
export interface DbConfig {
  db_type: string;
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  extra_params?: Record<string, unknown>;
}

/** Chat response from POST /v1/chat */
export interface ChatResponse {
  message?: string;
  sql?: string;
  explanation?: string;
  [key: string]: unknown;
}

/** Query execute result from POST /v1/query/execute */
export interface QueryResult {
  kind: "result_set" | "non_query";
  columns?: string[];
  rows?: Record<string, unknown>[];
  row_count?: number;
  affected_rows?: number;
}

/** Schema response from POST /v1/schema */
export interface SchemaResponse {
  tables: { table_name: string; columns: { name: string; type?: string }[] }[];
  total_tables?: number;
  [key: string]: unknown;
}
