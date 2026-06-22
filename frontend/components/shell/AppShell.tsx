"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";
import { useAuth } from "@/components/auth/AuthProvider";
import { Button } from "@/components/ui";

interface NavItem {
  href: string;
  label: string;
  icon: ReactNode;
  // Active when the path equals href, or (for non-root) starts with href.
  match: (pathname: string) => boolean;
}

const NAV: NavItem[] = [
  {
    href: "/",
    label: "Runs",
    match: (p) => p === "/" || p.startsWith("/runs"),
    icon: (
      <svg width="16" height="16" viewBox="0 0 20 20" fill="none" aria-hidden>
        <rect x="3" y="4" width="14" height="3" rx="1" stroke="currentColor" strokeWidth="1.4" />
        <rect x="3" y="9" width="14" height="3" rx="1" stroke="currentColor" strokeWidth="1.4" />
        <rect x="3" y="14" width="9" height="2.5" rx="1" stroke="currentColor" strokeWidth="1.4" />
      </svg>
    ),
  },
];

function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden w-[248px] shrink-0 flex-col bg-brand-ink text-white/70 md:flex">
      <div className="flex h-14 items-center gap-2.5 px-5">
        <span className="flex h-7 w-7 items-center justify-center rounded-md bg-white/10 text-xs font-bold text-white">
          KR
        </span>
        <span className="font-display text-sm font-bold tracking-tight text-white">RFP Console</span>
      </div>
      <nav className="flex flex-1 flex-col gap-0.5 p-3">
        <p className="px-2 pb-1.5 pt-2 text-2xs font-bold uppercase tracking-wider text-white/40">
          Sourcing
        </p>
        {NAV.map((item) => {
          const active = item.match(pathname);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-2.5 rounded-control px-2.5 py-2 text-sm transition-colors",
                active
                  ? "bg-white/10 font-semibold text-white"
                  : "text-white/65 hover:bg-white/5 hover:text-white",
              )}
            >
              <span className={active ? "text-white" : "text-white/45"}>{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="px-4 py-3 text-2xs text-white/40">Enterprise RFP sourcing</div>
    </aside>
  );
}

function Header() {
  const { user, logout } = useAuth();
  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-4 border-b border-border bg-surface-card px-5">
      <div className="flex items-center gap-2 md:hidden">
        <span className="flex h-7 w-7 items-center justify-center rounded-md bg-brand-primary text-xs font-bold text-white">
          KR
        </span>
        <span className="font-display text-sm font-bold text-text-strong">RFP Console</span>
      </div>
      <div className="hidden md:block" />
      <div className="flex items-center gap-3">
        {user && (
          <div className="flex items-center gap-2.5">
            <span
              className="flex h-8 w-8 items-center justify-center rounded-full bg-surface-muted text-xs font-bold text-text-muted"
              aria-hidden
            >
              {user.username.slice(0, 2).toUpperCase()}
            </span>
            <div className="leading-tight">
              <p className="text-sm font-semibold text-text-strong">{user.username}</p>
              <p className="text-2xs text-text-subtle">
                {user.totp_enabled ? "2FA enabled" : "Signed in"}
              </p>
            </div>
          </div>
        )}
        <Button variant="secondary" size="sm" onClick={() => void logout()}>
          Log out
        </Button>
      </div>
    </header>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header />
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-6xl px-5 py-6 lg:px-8">{children}</div>
        </main>
      </div>
    </div>
  );
}
