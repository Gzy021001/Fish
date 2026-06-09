import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'node:path'
import autoprefixer from 'autoprefixer'
import tailwindcss from 'tailwindcss'

export default defineConfig({
  plugins: [vue()],
  publicDir: 'public',
  css: {
    postcss: {
      plugins: [
        tailwindcss({ config: './tailwind.mobile.config.js' }),
        autoprefixer(),
      ],
    },
  },
  esbuild: {
    drop: ['console', 'debugger']
  },
  build: {
    outDir: 'dist-mobile',
    emptyOutDir: true,
    target: 'es2017',
    rollupOptions: {
      input: {
        mobile: resolve(__dirname, 'mobile.html')
      }
    }
  },
  server: {
    host: '0.0.0.0',
    port: 5176,
    strictPort: true,
    hmr: {
      protocol: 'ws',
      host: 'localhost',
      port: 5176,
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/uploads': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  }
})
