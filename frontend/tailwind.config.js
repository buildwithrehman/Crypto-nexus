/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#F7931A", // Bitcoin Amber
        secondary: "#0D0D0D", // Carbon Black
        tertiary: "#E5820D", // Deep Amber Ochre
        neutral: "#F9F8F3", // Warm Ivory Canvas
        "surface-accent": "#F4F1EA", // Secondary background
        "structural-border": "#121212", // 1px structural framing
        "muted-ink": "#5A5852", // Subordinate metadata
      },
      fontFamily: {
        display: ["Oswald", "sans-serif"],
        body: ["Space Grotesk", "sans-serif"],
        mono: ["Space Mono", "monospace"],
      },
      spacing: {
        xs: "0.25rem",
        sm: "0.5rem",
        md: "1rem",
        lg: "1.5rem",
        xl: "2.5rem",
        gutter: "0px",
        "gutter-loose": "1.5rem",
        margin: "1.5rem",
        "margin-mobile": "1rem",
      },
    },
  },
  plugins: [],
}
