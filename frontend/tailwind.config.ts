import type { Config } from "tailwindcss";

// One accent colour, dark-friendly, data-dense (BUILD_SPEC §10).
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        accent: {
          DEFAULT: "#4f46e5",
          soft: "#6366f1",
        },
      },
    },
  },
  plugins: [],
};

export default config;
