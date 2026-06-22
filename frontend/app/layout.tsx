import "./globals.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Montserrat, Nunito } from "next/font/google";
import { AuthProvider } from "@/components/auth/AuthProvider";

// Display face (headings, metrics, numerics) + body/UI face — locked v2 design.
const montserrat = Montserrat({
  subsets: ["latin"],
  weight: ["600", "700", "800"],
  variable: "--font-montserrat",
  display: "swap",
});
const nunito = Nunito({
  subsets: ["latin"],
  weight: ["400", "600", "700", "800"],
  variable: "--font-nunito",
  display: "swap",
});

export const metadata: Metadata = {
  title: "KR_RFP Console",
  description: "Enterprise RFP sourcing console — pure client of the FastAPI backend.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${montserrat.variable} ${nunito.variable}`}>
      <body className="min-h-screen bg-surface-app font-sans text-ink antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
