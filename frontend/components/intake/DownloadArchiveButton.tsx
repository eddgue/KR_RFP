"use client";

import { useState } from "react";
import { ApiError, downloadRunArchive } from "@/lib/api";
import { Button } from "@/components/ui";
import type { ButtonProps } from "@/components/ui";

export interface DownloadArchiveButtonProps {
  slug: string;
  variant?: ButtonProps["variant"];
  size?: ButtonProps["size"];
  className?: string;
}

function DownloadIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 20 20" fill="none" aria-hidden>
      <path
        d="M10 3v9m0 0 3.5-3.5M10 12 6.5 8.5M4 15h12"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// "Download run folder (.zip)" — authenticated archive download with inline
// error surfacing (never navigates away on failure).
export function DownloadArchiveButton({
  slug,
  variant = "secondary",
  size = "md",
  className,
}: DownloadArchiveButtonProps) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onClick() {
    setError(null);
    setBusy(true);
    try {
      await downloadRunArchive(slug);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail || "Could not download the run folder."
          : "Could not download the run folder.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <Button
        variant={variant}
        size={size}
        className={className}
        loading={busy}
        onClick={() => void onClick()}
      >
        <DownloadIcon />
        Download run folder (.zip)
      </Button>
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}
