"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export function Nav() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const isAuthPage = pathname === "/login" || pathname === "/register";

  return (
    <nav className="border-b border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800">
      <div className="container mx-auto flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-6">
          <Link
            href={user ? "/" : "/login"}
            className="text-lg font-semibold text-slate-800 hover:text-indigo-600 dark:text-slate-100 dark:hover:text-indigo-400"
          >
            AI Database Copilot
          </Link>
          {!isAuthPage && user && (
            <>
              <Link
                href="/"
                className="text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
              >
                Home
              </Link>
              <Link
                href="/chat"
                className="text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
              >
                Chat
              </Link>
              <Link
                href="/sql"
                className="text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
              >
                SQL Editor
              </Link>
              <Link
                href="/explorer"
                className="text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
              >
                Explorer
              </Link>
              <Link
                href="/upload"
                className="text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
              >
                Import
              </Link>
            </>
          )}
        </div>
        {!isAuthPage && (
          <div className="flex items-center gap-4">
            {user ? (
              <>
                <span className="text-sm text-slate-500 dark:text-slate-400">
                  {user.name || user.email}
                </span>
                <button
                  type="button"
                  onClick={() => logout()}
                  className="text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                >
                  Sign out
                </button>
              </>
            ) : (
              <Link
                href="/login"
                className="text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
              >
                Sign in
              </Link>
            )}
          </div>
        )}
      </div>
    </nav>
  );
}
