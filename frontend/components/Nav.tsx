"use client";

import Link from "next/link";

export function Nav() {
  return (
    <nav className="border-b border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800">
      <div className="container mx-auto flex items-center gap-6 px-4 py-3">
        <Link
          href="/"
          className="text-lg font-semibold text-slate-800 hover:text-indigo-600 dark:text-slate-100 dark:hover:text-indigo-400"
        >
          AI DB Tool
        </Link>
        <div className="flex gap-4">
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
        </div>
      </div>
    </nav>
  );
}
