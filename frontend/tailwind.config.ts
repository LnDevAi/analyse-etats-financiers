import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          50: "#f0f4ff",
          100: "#dde7ff",
          200: "#c3d2fe",
          300: "#9db3fd",
          400: "#7089fb",
          500: "#4f63f6",
          600: "#3a44eb",
          700: "#3035d8",
          800: "#2b2fae",
          900: "#292e89",
          950: "#1e293b",
        },
        risk: {
          vert: "#16a34a",
          orange: "#d97706",
          rouge: "#dc2626",
        },
      },
      backgroundColor: {
        base: "#F8FAFC",
      },
    },
  },
  plugins: [],
};

export default config;
