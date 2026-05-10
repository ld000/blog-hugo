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
          bg: "#010102",
          surface: "#0f1011",
          surfaceHover: "#141516",
          border: "#23252a",
          borderStrong: "#34343a",
          text: "#f7f8f8",
          muted: "#d0d6e0",
          subtle: "#8a8f98",
          accent: "#5e6ad2",
        },
      },
      fontFamily: {
        sans: ["Inter", '"SF Pro Display"', "-apple-system", "BlinkMacSystemFont", '"Segoe UI"', "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", '"SF Mono"', "Menlo", "monospace"],
      },
      fontSize: {
        technical: ["0.9rem", { lineHeight: "1.75" }],
      },
      letterSpacing: {
        linear: "0",
      },
      backgroundImage: {
        "dot-matrix": "none",
      },
      backgroundSize: {
        matrix: "18px 18px",
      },
      boxShadow: {
        "linear-hover": "inset 0 1px 0 rgba(247, 248, 248, 0.045)",
        "linear-cyan": "inset 0 1px 0 rgba(247, 248, 248, 0.045)",
        "linear-pink": "inset 0 1px 0 rgba(247, 248, 248, 0.045)",
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
          background: "#0f1011",
          border: "1px solid #23252a",
          boxShadow: "inset 0 1px 0 rgba(247, 248, 248, 0.045)",
        },
        ".hover-linear": {
          transition:
            "filter 160ms ease, box-shadow 160ms ease, border-color 160ms ease, background-color 160ms ease",
        },
        ".hover-linear:hover": {
          background: "#141516",
          boxShadow: "inset 0 1px 0 rgba(247, 248, 248, 0.045)",
        },
        ".bg-dot-matrix": {
          backgroundImage: "none",
          backgroundColor: "#010102",
        },
      });
    }),
  ],
};
