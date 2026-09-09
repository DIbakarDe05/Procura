/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#eef2f7',
          100: '#d5dde8',
          200: '#adbdd3',
          300: '#849cbd',
          400: '#5c7ba7',
          500: '#3a5f8a',
          600: '#2a4a6e',
          700: '#1a3664',
          800: '#122849',
          900: '#0b1a30',
        },
        saffron: {
          50: '#fdf2ef',
          100: '#f9ddd4',
          200: '#f3b9a8',
          300: '#e8917a',
          400: '#d9704f',
          500: '#c8553d',
          600: '#a84332',
          700: '#863427',
          800: '#66261e',
          900: '#471a15',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
