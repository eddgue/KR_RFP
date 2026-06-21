import "./globals.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";
import { AuthProvider } from "@/components/auth/AuthProvider";

export const metadata: Metadata = {
  title: "KR_RFP Console",
  description: "Enterprise RFP sourcing console — pure client of the FastAPI backend.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-surface-subtle text-ink">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
