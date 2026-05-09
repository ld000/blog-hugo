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
          surface: "rgba(255, 255, 255, 0.03)",
          border: "rgba(255, 255, 255, 0.08)",
          text: "#FFFFFF",
          muted: "rgba(255, 255, 255, 0.62)",
        },
        neon: {
          cyan: "#00F3FF",
          pink: "#FF00FF",
          green: "#39FF14",
          orange: "#FFA500",
        },
      },
      fontFamily: {
        sans: ['"Instrument Sans"', "Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "SFMono-Regular", "monospace"],
      },
      fontSize: {
        technical: ["0.9rem", { lineHeight: "1.75" }],
      },
      letterSpacing: {
        linear: "0",
      },
      backgroundImage: {
        "dot-matrix":
          "radial-gradient(circle, rgba(255,255,255,0.05) 1px, transparent 1px)",
      },
      backgroundSize: {
        matrix: "18px 18px",
      },
      boxShadow: {
        "linear-hover": "0 0 20px rgba(0, 243, 255, 0.1)",
        "linear-cyan": "0 0 20px rgba(0, 243, 255, 0.16)",
        "linear-pink": "0 0 20px rgba(255, 0, 255, 0.12)",
      },
      keyframes: {
        "linear-scanline": {
          "0%": { transform: "translateY(-120%)", opacity: "0" },
          "8%": { opacity: "0.02" },
          "100%": { transform: "translateY(120vh)", opacity: "0" },
        },
      },
      animation: {
        "linear-scanline": "linear-scanline 8s linear infinite",
      },
      backdropBlur: {
        linear: "10px",
      },
    },
  },
  plugins: [
    plugin(function ({ addUtilities }) {
      addUtilities({
        ".surface-linear": {
          background: "rgba(255, 255, 255, 0.03)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          "backdrop-filter": "blur(10px)",
        },
        ".hover-linear": {
          transition:
            "filter 160ms ease, box-shadow 160ms ease, border-color 160ms ease, background-color 160ms ease",
        },
        ".hover-linear:hover": {
          filter: "brightness(1.08)",
          boxShadow: "0 0 20px rgba(0, 243, 255, 0.1)",
        },
        ".bg-dot-matrix": {
          backgroundImage:
            "radial-gradient(circle, rgba(255,255,255,0.05) 1px, transparent 1px)",
          backgroundSize: "18px 18px",
        },
      });
    }),
  ],
};
