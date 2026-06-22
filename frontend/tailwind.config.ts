import type { Config } from "tailwindcss";

// Locked v2 design tokens (KR_RFP RFP Console): calm by default, gravity at
// exceptions and governed decisions. Legacy aliases (accent / ink / line /
// panel) are retained — pointed at the locked values — so in-flight components
// keep compiling during the E-26 re-skin; they're removed once migration lands.
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#084999",
          primary: "#084999",
          "primary-hover": "#0a5bbf",
          ink: "#0b1f3a", // navy sidebar / dark surfaces
          sky: "#2478ce", // focus ring + recommended-cell tint
        },
        // legacy alias -> brand primary
        accent: { DEFAULT: "#084999", hover: "#0a5bbf", soft: "#e8eff8" },
        text: {
          strong: "#102a4c",
          DEFAULT: "#16243d",
          muted: "#5b6b82",
          subtle: "#8a97a8",
          faint: "#9aa7b6",
        },
        // legacy alias -> text scale
        ink: { DEFAULT: "#16243d", strong: "#102a4c", muted: "#5b6b82", subtle: "#8a97a8" },
        surface: {
          DEFAULT: "#ffffff",
          app: "#eceff4",
          card: "#ffffff",
          subtle: "#f7f9fc",
          muted: "#eef0f3",
        },
        border: {
          DEFAULT: "#e3e8ef",
          hairline: "#eef1f5",
        },
        // legacy alias -> border
        line: { DEFAULT: "#e3e8ef", strong: "#cdd3dc", hairline: "#eef1f5" },
        success: { DEFAULT: "#1a7a4f", bg: "#e7f3ea" },
        warning: { DEFAULT: "#c98a1a", bg: "#fdf6e8" },
        danger: { DEFAULT: "#b3261e", bg: "#fbe9e7" },
        sealed: { DEFAULT: "#1d4ed8", bg: "#eef4ff" },
      },
      fontFamily: {
        display: ["var(--font-montserrat)", "ui-sans-serif", "system-ui", "sans-serif"],
        sans: ["var(--font-nunito)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      fontSize: {
        "2xs": ["0.6875rem", { lineHeight: "1rem" }],
      },
      boxShadow: {
        card: "0 1px 3px rgba(16,42,76,.05)",
        raised: "0 2px 8px rgba(8,73,153,.14)",
        panel: "0 1px 3px rgba(16,42,76,.05)", // legacy alias -> card
        modal: "0 24px 64px rgba(16,42,76,.3)",
      },
      borderRadius: {
        control: "8px",
        card: "12px",
        modal: "14px",
        pill: "20px",
        panel: "12px", // legacy alias -> card
      },
    },
  },
  plugins: [],
};

export default config;
