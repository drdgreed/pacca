/** @type {import('tailwindcss').Config} */

/**
 * Tailwind configuration — LAYOUT UTILITIES ONLY.
 *
 * PACCA's visual identity is owned by the Editorial-Clinical theme
 * in src/styles/theme.css (CSS custom properties + .sme-* utility
 * classes). Tailwind is retained for layout utilities — flex, grid,
 * gap-*, p-*, m-*, etc. — that have no aesthetic opinion.
 *
 * Color + typography customization deliberately not extended here.
 * Use the theme.css CSS variables instead:
 *
 *   ❌  className="bg-indigo-700 text-white"     ← do not use
 *   ✅  className="sme-button"                   ← use this
 *
 *   ❌  className="bg-success-50 text-success-600" ← do not use
 *   ✅  <StatusInk outcome="approved">…</StatusInk> ← use this
 *
 * Previously (pre-PR-UI-5) extended `colors:` with custom primary /
 * success / warning / danger palettes. Removed in PR-UI-5 once the
 * UI-convergence migration retired every consumer of those tokens.
 */

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
