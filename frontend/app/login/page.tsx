"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, login } from "@/lib/api";
import { useAuth } from "@/components/auth/AuthProvider";
import { Button, FormField, Input } from "@/components/ui";

function LockIcon({ className }: { className?: string }) {
  return (
    <svg
      width="13"
      height="13"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <rect x="5" y="11" width="14" height="9" rx="2" />
      <path d="M8 11V8a4 4 0 0 1 8 0v3" />
    </svg>
  );
}

function BackIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M15 18l-6-6 6-6" />
    </svg>
  );
}

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

  // Return to the credentials step from the 2FA screen.
  function backToCredentials() {
    if (submitting) return;
    setTotpRequired(false);
    setTotpCode("");
    setError(null);
  }

  return (
    <main className="flex min-h-screen">
      {/* ===== BRAND PANEL ===== */}
      <div
        className="relative hidden w-[46%] flex-none flex-col justify-between overflow-hidden bg-brand-ink px-[52px] py-12 text-white lg:flex"
        style={{
          backgroundImage:
            "radial-gradient(900px 500px at 18% 12%, rgba(36,120,206,.30), transparent 60%), radial-gradient(700px 500px at 90% 100%, rgba(8,73,153,.40), transparent 55%)",
        }}
      >
        <div className="flex items-center gap-4">
          <span className="flex h-9 w-9 items-center justify-center rounded-control bg-brand-primary font-display text-sm font-bold text-white">
            KR
          </span>
          <span className="h-5 w-px bg-white/20" aria-hidden />
          <span className="font-display text-base font-bold tracking-tight text-white">
            RFP Console
          </span>
        </div>

        <div>
          <h1 className="max-w-[440px] text-balance font-display text-[34px] font-extrabold leading-[1.18] tracking-tight text-white">
            Produce sourcing, run end to end.
          </h1>
          <p className="mt-4 max-w-[430px] text-[15px] leading-relaxed text-white/60">
            Set up cycles, intake bids, compare seven scenario lenses, and freeze
            governed awards — with every decision recommended by the engine and
            asserted by a human.
          </p>
          <div className="mt-7 flex flex-wrap gap-2.5">
            <span className="inline-flex items-center gap-1.5 rounded-control border border-white/10 bg-white/[0.07] px-3 py-1.5 text-xs font-semibold text-white/80">
              Decision-support · not auto-decided
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-control border border-white/10 bg-white/[0.07] px-3 py-1.5 text-xs font-semibold text-white/80">
              Audit-evented · hash-chained
            </span>
          </div>
        </div>

        <div className="text-xs text-white/40">
          Enterprise RFP sourcing · Kroger
        </div>
      </div>

      {/* ===== FORM PANEL ===== */}
      <div className="flex flex-1 items-center justify-center bg-surface-app px-6 py-10">
        <div className="w-full max-w-[380px]">
          {/* Compact brand lockup for the narrow viewport (brand panel hidden). */}
          <div className="mb-6 flex items-center justify-center gap-2.5 lg:hidden">
            <span className="flex h-9 w-9 items-center justify-center rounded-control bg-brand-primary font-display text-sm font-bold text-white">
              KR
            </span>
            <span className="font-display text-lg font-bold text-text-strong">
              RFP Console
            </span>
          </div>

          <div className="rounded-card border border-border bg-surface-card px-8 pb-7 pt-8 shadow-card">
            {!totpRequired ? (
              <>
                <h2 className="font-display text-xl font-extrabold text-text-strong">
                  Sign in
                </h2>
                <p className="mt-1 text-sm text-text-muted">
                  Access the enterprise produce-sourcing console.
                </p>
              </>
            ) : (
              <>
                <button
                  type="button"
                  onClick={backToCredentials}
                  disabled={submitting}
                  className="mb-4 inline-flex items-center gap-1.5 rounded-control text-xs font-bold text-text-subtle transition-colors hover:text-text disabled:opacity-55"
                >
                  <BackIcon />
                  Back
                </button>
                <div className="mb-3.5 flex h-11 w-11 items-center justify-center rounded-card bg-sealed-bg text-brand-primary">
                  <LockIcon className="h-[21px] w-[21px]" />
                </div>
                <h2 className="font-display text-xl font-extrabold text-text-strong">
                  Two-factor code
                </h2>
                <p className="mt-1 text-sm text-text-muted">
                  Enter the 6-digit code from your authenticator app
                  {username.trim() ? (
                    <>
                      {" "}for{" "}
                      <b className="font-semibold text-text">{username.trim()}</b>
                    </>
                  ) : null}
                  .
                </p>
              </>
            )}

            <form className="mt-6 flex flex-col gap-4" onSubmit={onSubmit} noValidate>
              {!totpRequired ? (
                <>
                  <FormField label="Username" htmlFor="username" required>
                    <Input
                      id="username"
                      name="username"
                      autoComplete="username"
                      placeholder="dana.ellison"
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
                      placeholder="••••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      disabled={submitting}
                      required
                    />
                  </FormField>
                </>
              ) : (
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
                    className="h-12 text-center font-display text-xl font-extrabold tracking-[0.5em] text-text-strong"
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
                  className="rounded-control border border-danger/30 bg-danger-bg px-3 py-2 text-sm text-danger"
                >
                  {error}
                </div>
              )}

              <Button type="submit" loading={submitting} className="mt-1 w-full">
                {totpRequired ? "Verify & sign in" : "Continue"}
              </Button>
            </form>
          </div>

          <div className="mt-4 flex items-center justify-center gap-1.5 text-xs text-text-subtle">
            <LockIcon />
            Sessions are secured with httpOnly cookies.
          </div>
        </div>
      </div>
    </main>
  );
}
