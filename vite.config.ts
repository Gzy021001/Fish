import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      imports: ['vue', 'vue-router', 'vue-i18n', 'pinia'],
      dirs: ['src/composables', 'src/stores'],
      dts: 'src/auto-imports.d.ts',
    }),
  ],
  esbuild: {
    drop: ['console', 'debugger']
  },
  build: {
    target: 'es2015',
    minify: 'esbuild',
    cssCodeSplit: true,
    sourcemap: false,
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'pinia', 'vue-i18n'],
          'echarts-vendor': ['echarts'],
          'xlsx-vendor': ['xlsx']
        }
      }
    }
  },
  server: {
    // 允许通过所有 IP 和 Host 访问，防止跨域问题
    host: '0.0.0.0',
    port: 5175,
    strictPort: true, // 强制使用指定端口，避免多开服务时 WebSocket 端口获取错乱
    hmr: {
      protocol: 'ws',
      host: 'localhost',
      port: 5175,
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000', // 转发给后端服务
        changeOrigin: true,
        // 保证架构的简单和健壮：这里不需要 rewrite，因为我们后端代码里的路由已经带了 /api 前缀。
        // 即前端请求 /api/species 会被代理到 http://127.0.0.1:8000/api/species，完美匹配
      },
      '/uploads': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  }
})
