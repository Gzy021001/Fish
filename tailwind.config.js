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
          // 主色：紫檀（原 #5c4033）
          blue: '#4a3428',
          // 松绿 / 琉璃（原 #5a7d5a）
          green: '#4e6a55',
          // 鎏金（原 #c4a35a）
          yellow: '#bfa05f',
          // 赭石（原 #b87333）
          orange: '#a9763f',
          // 朱砂（原 #a0522d）
          red: '#9c3b2e',
          // 宣纸（原 #f5efe0）
          bg: '#f6f1e6',
          // 素白（原 #fdfaf3）
          card: '#fdfbf5',
          // 墨（原 #3d3226）
          text: '#362b21',
          // 新增：细金线 / 深檀 / 淡金
          gold: '#c9a96a',
          ink: '#2e251d',
          sand: '#e6d3a6',
        },
      },
      fontFamily: {
        sans: ['"Microsoft YaHei"', '"PingFang SC"', '"Noto Sans SC"', 'sans-serif'],
        // 标题改宋体系，弱化「后台感」，更端庄
        serif: ['"Songti SC"', '"STSong"', '"SimSun"', '"Noto Serif SC"', '"Microsoft YaHei"', 'serif'],
      },
      boxShadow: {
        // 卡片阴影统一改成偏暖的檀色投影，替代默认灰影
        md: '0 1px 2px rgba(74, 52, 40, 0.05), 0 12px 28px -16px rgba(74, 52, 40, 0.28)',
        lg: '0 2px 4px rgba(74, 52, 40, 0.06), 0 18px 40px -20px rgba(74, 52, 40, 0.32)',
      },
    },
  },
  plugins: [],
}
