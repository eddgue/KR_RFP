import type { ReactNode } from "react";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { AppShell } from "@/components/shell/AppShell";

// Every route in this group is protected: AuthGuard enforces GET /auth/me and
// redirects to /login on 401, AppShell provides the left nav + header.
export default function AppGroupLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard>
      <AppShell>{children}</AppShell>
    </AuthGuard>
  );
}
