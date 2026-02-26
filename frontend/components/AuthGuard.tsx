"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/auth-context";

const PUBLIC_PATHS = ["/login", "/register", "/forgot-password", "/reset-password"];

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isReady } = useAuth();

  useEffect(() => {
    if (!isReady) return;
    if (PUBLIC_PATHS.includes(pathname ?? "")) return;
    if (!user) {
      router.replace("/login");
    }
  }, [isReady, user, pathname, router]);

  if (!isReady) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <p className="text-slate-500 dark:text-slate-400">Loading…</p>
      </div>
    );
  }
  if (PUBLIC_PATHS.includes(pathname ?? "")) {
    return <>{children}</>;
  }
  if (!user) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <p className="text-slate-500 dark:text-slate-400">Redirecting to sign in…</p>
      </div>
    );
  }
  return <>{children}</>;
}
