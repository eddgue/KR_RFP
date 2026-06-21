"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, login } from "@/lib/api";
import { useAuth } from "@/components/auth/AuthProvider";
import { Button, FormField, Input } from "@/components/ui";

export default function LoginPage() {
  const router = useRouter();
  const { status, refresh } = useAuth();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [totpCode, setTotpCode] = useState("");
  // Becomes true after the backend answers 401 "2FA code required".
  const [totpRequired, setTotpRequired] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // If a session already exists (e.g. user navigates to /login while signed in),
  // bounce to the dashboard.
  useEffect(() => {
    if (status === "authenticated") {
      router.replace("/");
    }
  }, [status, router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login({
        username: username.trim(),
        password,
        // Only send the code once the field is in play and filled.
        totp_code: totpRequired && totpCode ? totpCode.trim() : undefined,
      });
      // Cookie is set; refresh auth state then route to the dashboard.
      await refresh();
      router.replace("/");
    } catch (err) {
      if (err instanceof ApiError && err.twoFactorRequired) {
        // Reveal the TOTP field and let the user resubmit.
        setTotpRequired(true);
        setError(null);
      } else if (err instanceof ApiError) {
        setError(
          err.status === 401
            ? "Incorrect username, password, or 2FA code."
            : err.detail || "Sign in failed. Please try again.",
        );
      } else {
        setError("Unexpected error. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-surface-subtle px-4 py-12">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex items-center justify-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-md bg-accent text-sm font-bold text-white">
            KR
          </span>
          <span className="text-lg font-semibold text-ink">RFP Console</span>
        </div>

        <div className="rounded-panel border border-line bg-surface p-6 shadow-panel">
          <h1 className="text-lg font-semibold text-ink">Sign in</h1>
          <p className="mt-1 text-sm text-ink-muted">
            Access the enterprise RFP sourcing console.
          </p>

          <form className="mt-6 flex flex-col gap-4" onSubmit={onSubmit} noValidate>
            <FormField label="Username" htmlFor="username" required>
              <Input
                id="username"
                name="username"
                autoComplete="username"
                autoFocus
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={submitting}
                required
              />
            </FormField>

            <FormField label="Password" htmlFor="password" required>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={submitting}
                required
              />
            </FormField>

            {totpRequired && (
              <FormField
                label="Authentication code"
                htmlFor="totp"
                required
                hint="Enter the 6-digit code from your authenticator app."
              >
                <Input
                  id="totp"
                  name="totp"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  pattern="[0-9]*"
                  maxLength={6}
                  placeholder="000000"
                  className="tracking-[0.5em]"
                  autoFocus
                  value={totpCode}
                  onChange={(e) =>
                    setTotpCode(e.target.value.replace(/\D/g, "").slice(0, 6))
                  }
                  disabled={submitting}
                  required
                />
              </FormField>
            )}

            {error && (
              <div
                role="alert"
                className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
              >
                {error}
              </div>
            )}

            <Button type="submit" loading={submitting} className="mt-1 w-full">
              {totpRequired ? "Verify & sign in" : "Sign in"}
            </Button>
          </form>
        </div>

        <p className="mt-4 text-center text-2xs text-ink-subtle">
          Sessions are secured with httpOnly cookies.
        </p>
      </div>
    </main>
  );
}
