"use client";

import { DbConfigProvider } from "@/lib/db-config";

export function Providers({ children }: { children: React.ReactNode }) {
  return <DbConfigProvider>{children}</DbConfigProvider>;
}
