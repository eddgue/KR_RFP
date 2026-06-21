"use client";

import { useEffect } from "react";
import type { ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "./AuthProvider";

// Wraps protected app routes. While the session check is in flight, shows a
// calm loading state; if unauthenticated, redirects to /login and renders nothing.
export function AuthGuard({ children }: { children: ReactNode }) {
  const { status } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (status === "unauthenticated") {
      router.replace("/login");
    }
  }, [status, router]);

  if (status === "authenticated") {
    return <>{children}</>;
  }

  return (
    <div className="flex h-screen items-center justify-center">
      <div className="flex items-center gap-3 text-sm text-ink-muted">
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-line-strong border-t-accent" />
        {status === "loading" ? "Checking your session…" : "Redirecting to sign in…"}
      </div>
    </div>
  );
}
