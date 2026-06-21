"use client";

import { useId, useRef } from "react";
import { cn } from "@/lib/cn";

export interface FileInputProps {
  // The currently-selected file, owned by the parent.
  file: File | null;
  onChange: (file: File | null) => void;
  accept?: string;
  disabled?: boolean;
  className?: string;
  // Label shown on the "choose" button when no file is selected.
  buttonLabel?: string;
}

function FileIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 20 20" fill="none" aria-hidden>
      <path
        d="M11 2H5.5A1.5 1.5 0 0 0 4 3.5v13A1.5 1.5 0 0 0 5.5 18h9a1.5 1.5 0 0 0 1.5-1.5V7l-5-5Z"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
      <path d="M11 2v5h5" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
    </svg>
  );
}

// A styled file picker that matches the system's Input/Button look. The native
// <input type="file"> is visually hidden; the wrapping label drives it. Selection
// state is controlled by the parent so it can be reset after an upload.
export function FileInput({
  file,
  onChange,
  accept = ".xlsx",
  disabled,
  className,
  buttonLabel = "Choose file",
}: FileInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const id = useId();

  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-md border border-line-strong bg-white px-3 py-2",
        disabled && "cursor-not-allowed bg-surface-muted opacity-70",
        className,
      )}
    >
      <label
        htmlFor={id}
        className={cn(
          "inline-flex h-8 shrink-0 cursor-pointer items-center gap-2 rounded-md border border-line-strong bg-white px-3 text-sm font-medium text-ink transition-colors hover:bg-surface-muted",
          disabled && "pointer-events-none opacity-70",
        )}
      >
        <FileIcon />
        {buttonLabel}
      </label>
      <input
        ref={inputRef}
        id={id}
        type="file"
        accept={accept}
        disabled={disabled}
        className="sr-only"
        onChange={(e) => onChange(e.target.files?.[0] ?? null)}
      />
      <span
        className={cn(
          "min-w-0 flex-1 truncate text-sm",
          file ? "text-ink" : "text-ink-subtle",
        )}
      >
        {file ? file.name : "No file selected"}
      </span>
      {file && !disabled && (
        <button
          type="button"
          aria-label="Clear selected file"
          className="-mr-1 shrink-0 rounded-md p-1 text-ink-subtle hover:bg-surface-muted hover:text-ink"
          onClick={() => {
            onChange(null);
            if (inputRef.current) inputRef.current.value = "";
          }}
        >
          <svg width="16" height="16" viewBox="0 0 20 20" fill="none" aria-hidden>
            <path
              d="M5 5l10 10M15 5L5 15"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
            />
          </svg>
        </button>
      )}
    </div>
  );
}
