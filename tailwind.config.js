const plugin = require("tailwindcss/plugin");

module.exports = {
  content: [
    "./layouts/**/*.html",
    "./content/**/*.{md,html}",
    "./assets/**/*.{js,css}",
    "./themes/blowfish/layouts/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        linear: {
          bg: "#111111",
          panel: "rgba(255, 255, 255, 0.06)",
          border: "rgba(255, 255, 255, 0.12)",
        },
        neon: {
          cyan: "#00F3FF",
          pink: "#FF00FF",
          green: "#39FF14",
          orange: "#FFA500",
        },
      },
      fontFamily: {
        sans: ['"Instrument Sans"', "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        "neon-cyan": "0 0 0 1px rgba(0, 243, 255, 0.36), 0 0 24px rgba(0, 243, 255, 0.28)",
        "neon-pink": "0 0 0 1px rgba(255, 0, 255, 0.34), 0 0 24px rgba(255, 0, 255, 0.24)",
        "neon-green": "0 0 0 1px rgba(57, 255, 20, 0.32), 0 0 24px rgba(57, 255, 20, 0.2)",
      },
      dropShadow: {
        "neon-cyan": "0 0 12px rgba(0, 243, 255, 0.72)",
        "neon-pink": "0 0 12px rgba(255, 0, 255, 0.65)",
      },
      keyframes: {
        "neon-scan": {
          "0%": { transform: "translateY(-100%)", opacity: "0" },
          "8%": { opacity: "0.28" },
          "50%": { opacity: "0.18" },
          "100%": { transform: "translateY(100vh)", opacity: "0" },
        },
      },
      animation: {
        "neon-scan": "neon-scan 9s linear infinite",
      },
    },
  },
  plugins: [
    plugin(function ({ addUtilities }) {
      addUtilities({
        ".clip-cut-corners": {
          "clip-path":
            "polygon(0 12px, 12px 0, calc(100% - 12px) 0, 100% 12px, 100% calc(100% - 12px), calc(100% - 12px) 100%, 12px 100%, 0 calc(100% - 12px))",
        },
        ".glass-linear": {
          "background-color": "rgba(255, 255, 255, 0.06)",
          "border-color": "rgba(255, 255, 255, 0.12)",
          "backdrop-filter": "blur(18px)",
        },
      });
    }),
  ],
};
