import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        gd: {
          deep: "#0d0b14",
          panel: "#13111c",
          surface: "#1a1726",
          elevated: "#231f30",
          accent: "#7c6af6",
          "accent-hover": "#9585ff",
          "accent-muted": "#5a4db8",
          "text-primary": "#f0f0f3",
          "text-secondary": "#a8a3b8",
          "text-muted": "#6b6580",
          "text-dim": "#4a4460",
          safe: "#27a644",
          warn: "#e5a820",
          danger: "#ef4444",
          info: "#6b9fff",
        },
      },
      borderColor: {
        "gd-subtle": "rgba(255, 255, 255, 0.06)",
        "gd-standard": "rgba(255, 255, 255, 0.10)",
        "gd-accent": "rgba(124, 106, 246, 0.3)",
      },
      backgroundColor: {
        "gd-safe-bg": "rgba(39, 166, 68, 0.12)",
        "gd-warn-bg": "rgba(229, 168, 32, 0.12)",
        "gd-danger-bg": "rgba(239, 68, 68, 0.12)",
        "gd-info-bg": "rgba(107, 159, 255, 0.10)",
        "gd-accent-glow": "rgba(124, 106, 246, 0.15)",
        "gd-hover": "rgba(255, 255, 255, 0.04)",
        "gd-input": "rgba(255, 255, 255, 0.03)",
      },
      boxShadow: {
        "gd-card": "0 2px 8px rgba(0,0,0,0.25), 0 0 0 1px rgba(255,255,255,0.06)",
        "gd-elevated": "0 8px 24px rgba(0,0,0,0.35)",
        "gd-inset": "inset 0 1px 0 rgba(255,255,255,0.12), 0 1px 3px rgba(0,0,0,0.3)",
        "gd-focus": "0 0 0 3px rgba(124, 106, 246, 0.15)",
      },
      fontFamily: {
        sans: [
          "Inter Variable", "Inter", "SF Pro Display", "-apple-system",
          "system-ui", "Segoe UI", "Roboto", "sans-serif",
        ],
        mono: [
          "Berkeley Mono", "ui-monospace", "SF Mono", "Menlo", "monospace",
        ],
      },
    },
  },
  plugins: [],
};

export default config;
