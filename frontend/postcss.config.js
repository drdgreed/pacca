export default {
  plugins: {
    // Tailwind v4 moved the PostCSS plugin to its own package; v4 also
    // handles vendor prefixing internally, so autoprefixer is dropped.
    '@tailwindcss/postcss': {},
  },
}
