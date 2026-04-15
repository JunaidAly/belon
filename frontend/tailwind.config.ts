import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Sora", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        // Belon brand palette
        belon: {
          orange: "#f97316",
          "orange-dim": "rgba(249,115,22,0.15)",
          black: "#080808",
          surface: "#0d0e1a",
          border: "rgba(255,255,255,0.1)",
        },
      },
      animation: {
        "enter-up": "enter-up 0.35s ease-out both",
        "enter-x": "enter-x 0.35s ease-out both",
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        "enter-up": {
          from: { opacity: "0", transform: "translateY(12px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "enter-x": {
          from: { opacity: "0", transform: "translateX(-12px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
