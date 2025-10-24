/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0B0C10',
        primary: '#D4AF37',        // Rich gold matching company logo
        'primary-light': '#F4D03F', // Lighter gold for highlights
        'primary-dark': '#B8941E',  // Darker gold for depth
        secondary: '#1F2833',
        accent: '#66FCF1',
        text: '#C5C6C7',
        'text-dark': '#8B8C8D',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['Roboto Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
