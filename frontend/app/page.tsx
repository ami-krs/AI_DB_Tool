import Link from "next/link";
import { DbConnectionForm } from "@/components/DbConnectionForm";

export default function Home() {
  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100">
          AI Database Tool
        </h1>
        <p className="mt-2 text-slate-600 dark:text-slate-400">
          Connect a database, then use the AI Chatbot or SQL Editor to run
          queries.
        </p>
      </div>

      <section className="mx-auto max-w-2xl rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <h2 className="mb-4 text-lg font-semibold text-slate-800 dark:text-slate-100">
          Connect to a database
        </h2>
        <DbConnectionForm />
      </section>

      <div className="flex flex-wrap justify-center gap-4">
        <Link
          href="/chat"
          className="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700"
        >
          AI Chatbot
        </Link>
        <Link
          href="/sql"
          className="rounded-lg border border-slate-300 px-4 py-2 font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
        >
          SQL Editor
        </Link>
        <Link
          href="/explorer"
          className="rounded-lg border border-slate-300 px-4 py-2 font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
        >
          Data Explorer
        </Link>
      </div>
    </div>
  );
}
