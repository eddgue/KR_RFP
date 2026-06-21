import type { Config } from "tailwindcss";

// "Clean enterprise" palette — muted neutrals + a single restrained accent.
// Dense, calm, data-first. Tuned for compact tables and status chips.
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Neutral surface scale (cool gray).
        surface: {
          DEFAULT: "#ffffff",
          subtle: "#f7f8fa",
          muted: "#eef0f3",
        },
        ink: {
          DEFAULT: "#1c2530",
          muted: "#5b6573",
          subtle: "#8a93a1",
        },
        line: {
          DEFAULT: "#e2e6ec",
          strong: "#cdd3dc",
        },
        accent: {
          DEFAULT: "#2563a8",
          hover: "#1f5390",
          soft: "#e8f0f9",
        },
      },
      fontSize: {
        "2xs": ["0.6875rem", { lineHeight: "1rem" }],
      },
      boxShadow: {
        panel: "0 1px 2px rgba(16, 24, 40, 0.04), 0 1px 3px rgba(16, 24, 40, 0.06)",
        modal: "0 10px 38px rgba(16, 24, 40, 0.18), 0 3px 12px rgba(16, 24, 40, 0.10)",
      },
      borderRadius: {
        panel: "0.625rem",
      },
    },
  },
  plugins: [],
};

export default config;
