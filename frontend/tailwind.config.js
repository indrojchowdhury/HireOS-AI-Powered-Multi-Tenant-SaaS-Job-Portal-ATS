/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Core brand color palette for HireOS platform
        brand: {
          primary: '#1e3a8a',   // Dark corporate blue
          secondary: '#2563eb', // Royal blue for interactive elements
          accent: '#10b981',    // Emerald green for success states
          dark: '#0f172a',      // Slate 900 for dark text
          light: '#f8fafc',     // Slate 50 for page background
        }
      }
    },
  },
  plugins: [],
}