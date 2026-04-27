/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'aw-teal': '#5DCAA5',
        'aw-purple': '#AFA9EC',
        'aw-red': '#F09595',
        'aw-amber': '#EF9F27',
        'aw-amber-dim': '#B87C14',
        'aw-gray': '#888888',
      },
    },
  },
  plugins: [],
}
