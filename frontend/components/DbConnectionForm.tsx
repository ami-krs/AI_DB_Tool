"use client";

import { useState } from "react";
import { useDbConfig } from "@/lib/db-config";
import type { DbConfig } from "@/lib/types";
import { getSchema } from "@/lib/api";

export function DbConnectionForm() {
  const { dbConfig, setDbConfig, isConnected } = useDbConfig();
  const [dbType, setDbType] = useState(dbConfig?.db_type || "sqlite");
  const [host, setHost] = useState(dbConfig?.host || "");
  const [port, setPort] = useState(String(dbConfig?.port || "5432"));
  const [database, setDatabase] = useState(dbConfig?.database || "");
  const [username, setUsername] = useState(dbConfig?.username || "");
  const [password, setPassword] = useState(dbConfig?.password || "");
  const [error, setError] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const config: DbConfig = {
      db_type: dbType,
      host: host.trim(),
      port: parseInt(port, 10) || 0,
      database: database.trim(),
      username: username.trim(),
      password,
    };
    setTesting(true);
    try {
      await getSchema(config);
      setDbConfig(config);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connection failed");
    } finally {
      setTesting(false);
    }
  };

  const handleDisconnect = () => {
    setDbConfig(null);
    setHost("");
    setPort("5432");
    setDatabase("");
    setUsername("");
    setPassword("");
    setError(null);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
          {error}
        </div>
      )}
      {isConnected && dbConfig && (
        <div className="rounded-lg bg-green-50 p-3 text-sm text-green-800 dark:bg-green-900/20 dark:text-green-300">
          Connected to {dbConfig.database}
          <button
            type="button"
            onClick={handleDisconnect}
            className="ml-2 underline hover:no-underline"
          >
            Disconnect
          </button>
        </div>
      )}

      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
          Database type
        </label>
        <select
          value={dbType}
          onChange={(e) => setDbType(e.target.value)}
          className="w-full rounded border border-slate-300 bg-white px-3 py-2 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
        >
          <option value="sqlite">SQLite</option>
          <option value="postgresql">PostgreSQL</option>
          <option value="mysql">MySQL</option>
        </select>
      </div>

      {dbType !== "sqlite" && (
        <>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
              Host
            </label>
            <input
              type="text"
              value={host}
              onChange={(e) => setHost(e.target.value)}
              placeholder="localhost"
              className="w-full rounded border border-slate-300 px-3 py-2 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
              Port
            </label>
            <input
              type="text"
              value={port}
              onChange={(e) => setPort(e.target.value)}
              placeholder="5432"
              className="w-full rounded border border-slate-300 px-3 py-2 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded border border-slate-300 px-3 py-2 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded border border-slate-300 px-3 py-2 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
            />
          </div>
        </>
      )}

      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
          {dbType === "sqlite" ? "Database file path" : "Database name"}
        </label>
        <input
          type="text"
          value={database}
          onChange={(e) => setDatabase(e.target.value)}
          placeholder={dbType === "sqlite" ? "/path/to/database.sqlite" : "mydb"}
          className="w-full rounded border border-slate-300 px-3 py-2 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
        />
      </div>

      <button
        type="submit"
        disabled={testing || !database.trim()}
        className="w-full rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        {testing ? "Connecting…" : isConnected ? "Reconnect" : "Connect"}
      </button>
    </form>
  );
}
