"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { resetPasswordWithToken } from "@/lib/api";

export default function ResetPasswordPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token") ?? "";
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [invalidLink, setInvalidLink] = useState(false);

  useEffect(() => {
    if (typeof token !== "string" || token.length < 16) {
      setInvalidLink(true);
    }
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (newPassword.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    setLoading(true);
    try {
      await resetPasswordWithToken(token, newPassword);
      router.push("/login?reset=success");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reset password");
      setInvalidLink(true);
    } finally {
      setLoading(false);
    }
  };

  if (invalidLink && !loading) {
    return (
      <div className="mx-auto max-w-sm space-y-6 rounded-xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-600 dark:bg-slate-800">
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Invalid or expired link</h1>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          This reset link is invalid or has expired. Request a new one below.
        </p>
        <Link
          href="/forgot-password"
          className="block w-full rounded-lg bg-indigo-600 py-2 text-center font-medium text-white hover:bg-indigo-700"
        >
          Request new reset link
        </Link>
        <p className="text-center text-sm text-slate-600 dark:text-slate-400">
          <Link href="/login" className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400">
            Back to sign in
          </Link>
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-sm space-y-6 rounded-xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-600 dark:bg-slate-800">
      <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Set new password</h1>
      <p className="text-sm text-slate-600 dark:text-slate-400">
        Enter your new password below.
      </p>
      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
          {error}
        </div>
      )}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="reset-new-password" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
            New password
          </label>
          <input
            id="reset-new-password"
            type="password"
            autoComplete="new-password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-800 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
            placeholder="At least 6 characters"
            disabled={loading}
          />
        </div>
        <div>
          <label htmlFor="reset-confirm" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
            Confirm password
          </label>
          <input
            id="reset-confirm"
            type="password"
            autoComplete="new-password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-800 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
            placeholder="Repeat new password"
            disabled={loading}
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-indigo-600 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "Resetting…" : "Reset password"}
        </button>
      </form>
      <p className="text-center text-sm text-slate-600 dark:text-slate-400">
        <Link href="/login" className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}
