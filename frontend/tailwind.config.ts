import type { Config } from "tailwindcss";

/**
 * Scintia design system (docs/03_CHARTE_GRAPHIQUE.md).
 * Tokens are implemented verbatim. Dark mode is the default; theme-aware role
 * tokens (bg/surface/border/text/primary) are driven by CSS variables set in
 * app/globals.css so light mode (reports/PDF) flips the right values.
 */
const config: Config = {
  // Theme is driven by CSS variables (globals.css); dark is the default.
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // ── Scintia spectrum (cold → hot) ──
        halo: "#34E3E3",
        iris: { DEFAULT: "#6E6FFF", light: "#4B4DE0" },
        magenta: "#EC4899",
        amber: "#FFB13D",
        // ── Ink neutrals (reading room) ──
        ink: {
          1000: "#07090F",
          900: "#0B0E15",
          850: "#10141D",
          800: "#161B26",
          750: "#1C2230",
          700: "#262E3D",
          400: "#6B7689",
          300: "#98A2B3",
          200: "#C4CBD6",
          100: "#E7EAF0",
        },
        paper: "#F5F7FB",
        // ── Semantic ──
        ok: "#1FBF8F",
        info: "#34E3E3",
        warn: "#FFB13D",
        crit: "#FF4D6D",
        // ── Theme-aware role tokens (CSS vars in globals.css) ──
        bg: "var(--color-bg)",
        surface: "var(--color-surface)",
        border: "var(--color-border)",
        text: "var(--color-text)",
        muted: "var(--color-muted)",
        primary: "var(--color-primary)",
      },
      fontFamily: {
        display: ["var(--font-display)", "sans-serif"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      borderRadius: {
        sm: "10px",
        md: "14px",
        lg: "18px",
        xl: "20px",
        pill: "999px",
      },
      keyframes: {
        // Logo core "breathing" (charter §9). Honors prefers-reduced-motion.
        breathe: {
          "0%, 100%": { opacity: "0.82" },
          "50%": { opacity: "1" },
        },
      },
      animation: {
        breathe: "breathe 4.2s ease-in-out infinite",
      },
      backgroundImage: {
        grad: "linear-gradient(100deg, #34E3E3, #6E6FFF 38%, #EC4899 70%, #FFB13D)",
        "grad-hot": "linear-gradient(120deg, #6E6FFF, #EC4899 55%, #FFB13D)",
      },
      boxShadow: {
        soft: "0 40px 90px -50px rgba(0,0,0,.9)",
      },
      transitionTimingFunction: {
        soft: "cubic-bezier(0.22, 1, 0.36, 1)",
      },
    },
  },
  plugins: [],
};

export default config;
