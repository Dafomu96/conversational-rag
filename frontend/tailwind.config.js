export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        mono: ["'JetBrains Mono'", "monospace"],
        sans: ["'DM Sans'", "sans-serif"],
        display: ["'Syne'", "sans-serif"],
      },
      colors: {
        surface: {
          50: "#f8f7f4",
          100: "#f0ede6",
          900: "#1a1814",
          950: "#0f0e0c",
        },
        accent: {
          400: "#e8b84b",
          500: "#d4a535",
        },
      },
    },
  },
  plugins: [],
}