import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        guard: {
          900: "#0B1120",
          800: "#0F172A",
          700: "#1E293B",
          600: "#334155",
          accent: "#3B82F6",
          danger: "#EF4444",
          safe: "#10B981",
          warn: "#F59E0B",
        },
      },
    },
  },
  plugins: [],
};

export default config;
