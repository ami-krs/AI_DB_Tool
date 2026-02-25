"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import type { DbConfig } from "./types";

const STORAGE_KEY = "ai_db_tool_db_config";

function loadFromStorage(): DbConfig | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as DbConfig;
    return parsed && typeof parsed.db_type === "string" && typeof parsed.database === "string"
      ? parsed
      : null;
  } catch {
    return null;
  }
}

function saveToStorage(config: DbConfig | null) {
  if (typeof window === "undefined") return;
  if (config) localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
  else localStorage.removeItem(STORAGE_KEY);
}

type DbConfigContextValue = {
  dbConfig: DbConfig | null;
  setDbConfig: (config: DbConfig | null) => void;
  isConnected: boolean;
};

const DbConfigContext = createContext<DbConfigContextValue>({
  dbConfig: null,
  setDbConfig: () => {},
  isConnected: false,
});

export function DbConfigProvider({ children }: { children: React.ReactNode }) {
  const [dbConfig, setState] = useState<DbConfig | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setState(loadFromStorage());
    setMounted(true);
  }, []);

  const setDbConfig = useCallback((config: DbConfig | null) => {
    setState(config);
    saveToStorage(config);
  }, []);

  return (
    <DbConfigContext.Provider
      value={{
        dbConfig: mounted ? dbConfig : null,
        setDbConfig,
        isConnected: mounted && !!dbConfig,
      }}
    >
      {children}
    </DbConfigContext.Provider>
  );
}

export function useDbConfig() {
  return useContext(DbConfigContext);
}
