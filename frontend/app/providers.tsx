"use client";

import { AuthProvider } from "@/lib/auth-context";
import { DbConfigProvider } from "@/lib/db-config";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <DbConfigProvider>{children}</DbConfigProvider>
    </AuthProvider>
  );
}
