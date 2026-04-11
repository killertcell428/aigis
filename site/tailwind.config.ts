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
        guardian: {
          50:  "#eef5ff",
          100: "#d9e9ff",
          200: "#bcd6ff",
          300: "#8ebbff",
          400: "#5994ff",
          500: "#3370ff",
          600: "#1a4ff5",
          700: "#1340e1",
          800: "#1636b6",
          900: "#18318f",
          950: "#131f57",
        },
        accent: {
          red:    "#ef4444",
          orange: "#f97316",
          yellow: "#eab308",
          green:  "#22c55e",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};

export default config;
