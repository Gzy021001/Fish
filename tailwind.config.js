/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dunhuang: {
          blue: '#5c4033',
          green: '#5a7d5a',
          yellow: '#c4a35a',
          orange: '#b87333',
          red: '#a0522d',
          bg: '#f5efe0',
          card: '#fdfaf3',
          text: '#3d3226',
        }
      },
      fontFamily: {
        sans: ['"Microsoft YaHei"', '"PingFang SC"', '"Noto Sans SC"', 'sans-serif'],
        serif: ['"Microsoft YaHei"', '"Noto Serif SC"', '"Songti SC"', 'serif'],
      },
    },
  },
  plugins: [],
}
