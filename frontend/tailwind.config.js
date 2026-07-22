/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          purple: '#6C5CE7',
          blue: '#2563EB',
          red: '#DC2626',
          bg: '#F3F4F6'
        }
      }
    },
  },
  plugins: [],
}
