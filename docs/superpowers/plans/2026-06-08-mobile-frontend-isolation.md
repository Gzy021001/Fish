# Mobile Frontend Isolation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不修改现有 PC 端前端代码的前提下，为项目建立一套独立的移动端前端副本与构建入口，并为后续移动端适配扫清阻塞点。

**Architecture:** 保留现有 `src`、`index.html`、`vite.config.ts` 作为 PC 端稳定基线，不在其中做行为性修改。移动端通过新增 `src-mobile`、`mobile.html`、`vite.mobile.config.ts` 和独立本地存储 key 形成完全隔离的前端运行时；后端继续共用，但仅允许做向后兼容增强。

**Tech Stack:** Vue 3, Vite 5, Pinia, Vue Router, Vue I18n, Tailwind CSS, Axios, FastAPI

---

## File Map

### Existing Files To Keep Read-Only

- `d:\Fish\src\main.ts`：PC 端应用入口，保持不变
- `d:\Fish\src\router\index.ts`：PC 端路由，保持不变
- `d:\Fish\src\stores\auth.ts`：PC 端认证存储，保持不变
- `d:\Fish\src\style.css`：PC 端全局样式，保持不变
- `d:\Fish\index.html`：PC 端入口 HTML，保持不变
- `d:\Fish\vite.config.ts`：PC 端 Vite 配置，保持不变

### New Files To Create

- `d:\Fish\mobile.html`：移动端入口 HTML
- `d:\Fish\vite.mobile.config.ts`：移动端独立构建配置
- `d:\Fish\src-mobile\main.ts`：移动端入口
- `d:\Fish\src-mobile\App.vue`：移动端应用壳层
- `d:\Fish\src-mobile\router\index.ts`：移动端路由
- `d:\Fish\src-mobile\stores\auth.ts`：移动端认证存储，使用独立 localStorage key
- `d:\Fish\src-mobile\style.css`：移动端全局样式，加入安全区和触控基线
- `d:\Fish\src-mobile\pages\Login.vue`：从 PC 端复制后改为移动端布局
- `d:\Fish\src-mobile\pages\Dashboard.vue`：从 PC 端复制后改为移动端布局
- `d:\Fish\src-mobile\pages\Species.vue`：从 PC 端复制后改为移动端列表布局
- `d:\Fish\src-mobile\components\MobileLayout.vue`：移动端专属布局
- `d:\Fish\src-mobile\components\MobileTabBar.vue`：底部导航
- `d:\Fish\src-mobile\api\index.ts`：移动端 Axios 实例，可先复制后按需改 key/拦截器
- `d:\Fish\src-mobile\lib\storage.ts`：统一管理移动端 localStorage key
- `d:\Fish\src-mobile\vite-env.d.ts`：移动端类型声明
- `d:\Fish\docs\mobile-api-contract.md`：移动端 API 约束清单，明确后端不得破坏 PC 默认响应

### Existing Files Allowed To Reference But Not Edit

- `d:\Fish\src\api\index.ts`
- `d:\Fish\src\pages\Login.vue`
- `d:\Fish\src\pages\Dashboard.vue`
- `d:\Fish\src\pages\Species.vue`
- `d:\Fish\src\components\Layout.vue`

### Optional New Scripts File

- `d:\Fish\scripts\run-mobile-dev.ps1`：如果不想改 `package.json`，用脚本启动移动端开发服务器

---

### Task 1: 建立移动端文件边界

**Files:**
- Create: `d:\Fish\docs\mobile-api-contract.md`
- Test: 手工验证目录边界，不执行代码

- [ ] **Step 1: 写出边界约束文档**

```md
# Mobile API And Frontend Isolation Contract

## Frontend Boundary

- `src`、`index.html`、`vite.config.ts`、`src/router/index.ts`、`src/stores/auth.ts` 视为 PC 端冻结基线。
- 移动端只允许在 `src-mobile`、`mobile.html`、`vite.mobile.config.ts` 中开发。
- 禁止为了兼容移动端而回写 PC 端组件、页面、样式和路由。

## Backend Boundary

- 后端现有接口默认行为不得改变。
- 移动端需要更轻 payload 时，只能新增可选参数或新增移动端接口。
- 列表接口默认字段集合必须保持兼容 PC。

## Storage Boundary

- PC 端继续使用 `token`、`username`、`user_avatar`。
- 移动端使用 `mobile_token`、`mobile_username`、`mobile_user_avatar`。
```

- [ ] **Step 2: 目视检查约束是否满足当前目标**

Run:

```powershell
Get-Content d:\Fish\docs\mobile-api-contract.md
```

Expected: 文档中明确写出 `src` 只读、`src-mobile` 独立开发、后端只允许兼容增强。

- [ ] **Step 3: Commit**

```bash
git add d:/Fish/docs/mobile-api-contract.md
git commit -m "docs: define mobile isolation contract"
```

---

### Task 2: 新增移动端独立入口，不修改 PC 入口

**Files:**
- Create: `d:\Fish\mobile.html`
- Create: `d:\Fish\src-mobile\main.ts`
- Create: `d:\Fish\src-mobile\App.vue`
- Create: `d:\Fish\src-mobile\vite-env.d.ts`
- Test: `mobile.html` 能挂载 `#app`

- [ ] **Step 1: 创建移动端 HTML 入口**

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta
      name="viewport"
      content="width=device-width, initial-scale=1, viewport-fit=cover"
    />
    <title>Fish Mobile</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src-mobile/main.ts"></script>
  </body>
</html>
```

- [ ] **Step 2: 创建移动端应用入口**

```ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { i18n } from '../src/i18n'
import './style.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(i18n)

app.mount('#app')
```

- [ ] **Step 3: 创建移动端壳层组件**

```vue
<template>
  <router-view />
</template>
```

- [ ] **Step 4: 创建类型声明**

```ts
/// <reference types="vite/client" />
```

- [ ] **Step 5: 运行挂载检查**

Run:

```powershell
npx vite --config d:\Fish\vite.mobile.config.ts
```

Expected: 终端输出移动端 dev server 地址，页面打开后没有 `Failed to resolve /src-mobile/main.ts` 报错。

- [ ] **Step 6: Commit**

```bash
git add d:/Fish/mobile.html d:/Fish/src-mobile/main.ts d:/Fish/src-mobile/App.vue d:/Fish/src-mobile/vite-env.d.ts
git commit -m "feat: add mobile app entry"
```

---

### Task 3: 建立移动端独立构建配置

**Files:**
- Create: `d:\Fish\vite.mobile.config.ts`
- Create: `d:\Fish\scripts\run-mobile-dev.ps1`
- Test: 移动端入口通过独立配置启动

- [ ] **Step 1: 新建移动端 Vite 配置**

```ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'node:path'

export default defineConfig({
  plugins: [vue()],
  publicDir: 'public',
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
      port: 5176
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/uploads': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
```

- [ ] **Step 2: 如需零修改 `package.json`，增加启动脚本**

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
npx vite --config d:\Fish\vite.mobile.config.ts
```

- [ ] **Step 3: 运行独立配置验证**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File d:\Fish\scripts\run-mobile-dev.ps1
```

Expected: 仅启动移动端入口，PC 端 `vite.config.ts` 不被读取。

- [ ] **Step 4: Commit**

```bash
git add d:/Fish/vite.mobile.config.ts d:/Fish/scripts/run-mobile-dev.ps1
git commit -m "build: add isolated mobile vite config"
```

---

### Task 4: 复制并隔离认证与网络层

**Files:**
- Create: `d:\Fish\src-mobile\lib\storage.ts`
- Create: `d:\Fish\src-mobile\stores\auth.ts`
- Create: `d:\Fish\src-mobile\api\index.ts`
- Test: 登录态只写入移动端 key，不污染 PC key

- [ ] **Step 1: 定义移动端存储 key**

```ts
export const MOBILE_STORAGE_KEYS = {
  token: 'mobile_token',
  username: 'mobile_username',
  avatar: 'mobile_user_avatar'
} as const
```

- [ ] **Step 2: 创建移动端认证 store**

```ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { MOBILE_STORAGE_KEYS } from '../lib/storage'

export const useAuthStore = defineStore('mobile-auth', () => {
  const token = ref<string | null>(localStorage.getItem(MOBILE_STORAGE_KEYS.token))
  const username = ref<string | null>(localStorage.getItem(MOBILE_STORAGE_KEYS.username))

  function login(newToken: string, user: string) {
    token.value = newToken
    username.value = user
    localStorage.setItem(MOBILE_STORAGE_KEYS.token, newToken)
    localStorage.setItem(MOBILE_STORAGE_KEYS.username, user)
  }

  function logout() {
    token.value = null
    username.value = null
    localStorage.removeItem(MOBILE_STORAGE_KEYS.token)
    localStorage.removeItem(MOBILE_STORAGE_KEYS.username)
  }

  return { token, username, login, logout }
})
```

- [ ] **Step 3: 创建移动端 Axios 实例**

```ts
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import router from '../router'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 20000
})

api.interceptors.request.use(config => {
  const authStore = useAuthStore()
  if (authStore.token) {
    config.headers.Authorization = `Bearer ${authStore.token}`
  }
  return config
})

api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      router.replace('/login')
    }
    return Promise.reject(error)
  }
)

export default api
```

- [ ] **Step 4: 手工验证存储隔离**

Run:

```powershell
Get-Content d:\Fish\src-mobile\stores\auth.ts
```

Expected: 仅出现 `mobile_token`、`mobile_username`，没有写入 `token`、`username`。

- [ ] **Step 5: Commit**

```bash
git add d:/Fish/src-mobile/lib/storage.ts d:/Fish/src-mobile/stores/auth.ts d:/Fish/src-mobile/api/index.ts
git commit -m "feat: isolate mobile auth and api layer"
```

---

### Task 5: 复制移动端最小路由骨架

**Files:**
- Create: `d:\Fish\src-mobile\router\index.ts`
- Create: `d:\Fish\src-mobile\components\MobileLayout.vue`
- Create: `d:\Fish\src-mobile\components\MobileTabBar.vue`
- Test: 能访问 `/login`、`/dashboard`、`/species`

- [ ] **Step 1: 创建移动端路由**

```ts
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory('/mobile/'),
  routes: [
    {
      path: '/login',
      name: 'MobileLogin',
      component: () => import('../pages/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      component: () => import('../components/MobileLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/dashboard' },
        { path: 'dashboard', name: 'MobileDashboard', component: () => import('../pages/Dashboard.vue') },
        { path: 'species', name: 'MobileSpecies', component: () => import('../pages/Species.vue') }
      ]
    }
  ]
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.token) {
    next('/login')
    return
  }
  if (to.path === '/login' && authStore.token) {
    next('/dashboard')
    return
  }
  next()
})

export default router
```

- [ ] **Step 2: 创建移动端布局**

```vue
<template>
  <div class="min-h-screen flex flex-col bg-dunhuang-bg">
    <main class="flex-1 overflow-y-auto pb-[calc(64px+env(safe-area-inset-bottom))]">
      <router-view />
    </main>
    <MobileTabBar />
  </div>
</template>

<script setup lang="ts">
import MobileTabBar from './MobileTabBar.vue'
</script>
```

- [ ] **Step 3: 创建底部导航**

```vue
<template>
  <nav class="fixed bottom-0 inset-x-0 h-16 px-4 pb-[env(safe-area-inset-bottom)] bg-[#f5ead7] border-t border-[#d8c1a0] flex items-center justify-around">
    <RouterLink to="/dashboard">首页</RouterLink>
    <RouterLink to="/species">品种</RouterLink>
  </nav>
</template>
```

- [ ] **Step 4: 运行路由验证**

Run:

```powershell
npx vite --config d:\Fish\vite.mobile.config.ts
```

Expected: 打开移动端入口后能路由到 `/login`，登录态存在时可访问 `/dashboard` 和 `/species`。

- [ ] **Step 5: Commit**

```bash
git add d:/Fish/src-mobile/router/index.ts d:/Fish/src-mobile/components/MobileLayout.vue d:/Fish/src-mobile/components/MobileTabBar.vue
git commit -m "feat: add mobile routing skeleton"
```

---

### Task 6: 复制三张页面作为最小可运行切面

**Files:**
- Create: `d:\Fish\src-mobile\pages\Login.vue`
- Create: `d:\Fish\src-mobile\pages\Dashboard.vue`
- Create: `d:\Fish\src-mobile\pages\Species.vue`
- Test: 登录、首页、品种列表三条链路打通

- [ ] **Step 1: 复制 `Login.vue`，只保留移动端必需结构**

```vue
<template>
  <div class="min-h-screen flex items-center justify-center px-5 py-8">
    <form class="w-full max-w-sm space-y-4 rounded-2xl bg-white/90 p-5 shadow-lg" @submit.prevent="handleLogin">
      <h1 class="text-xl font-serif text-center">移动端登录</h1>
      <input v-model="username" class="w-full rounded-xl border px-4 py-3" placeholder="用户名" />
      <input v-model="password" type="password" class="w-full rounded-xl border px-4 py-3" placeholder="密码" />
      <button :disabled="loading" class="w-full rounded-xl bg-[#8b6914] py-3 text-white">
        {{ loading ? '登录中...' : '登录' }}
      </button>
      <p v-if="errorMsg" class="text-sm text-red-600">{{ errorMsg }}</p>
    </form>
  </div>
</template>
```

- [ ] **Step 2: 复制 `Dashboard.vue`，先裁成只读数据卡片**

```vue
<template>
  <section class="p-4 space-y-4">
    <h1 class="text-xl font-serif">首页</h1>
    <div class="rounded-2xl bg-white/90 p-4 shadow-sm">
      移动端首页骨架已接通
    </div>
  </section>
</template>
```

- [ ] **Step 3: 复制 `Species.vue`，先保留列表与分页**

```vue
<template>
  <section class="p-4 space-y-4">
    <h1 class="text-xl font-serif">品种</h1>
    <div class="rounded-2xl bg-white/90 p-4 shadow-sm">
      这里接入品种列表最小版
    </div>
  </section>
</template>
```

- [ ] **Step 4: 验证三条主链路**

Run:

```powershell
npx vite --config d:\Fish\vite.mobile.config.ts
```

Expected: 移动端入口可完成登录、跳转首页、访问品种页，不需要依赖 PC 布局组件。

- [ ] **Step 5: Commit**

```bash
git add d:/Fish/src-mobile/pages/Login.vue d:/Fish/src-mobile/pages/Dashboard.vue d:/Fish/src-mobile/pages/Species.vue
git commit -m "feat: scaffold mobile login dashboard and species pages"
```

---

### Task 7: 建立移动端样式基线，提前规避阻塞

**Files:**
- Create: `d:\Fish\src-mobile\style.css`
- Test: 安全区、滚动、触控反馈生效

- [ ] **Step 1: 创建移动端样式基线**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  html,
  body,
  #app {
    min-height: 100%;
  }

  body {
    margin: 0;
    background: #f7efe2;
    color: #5c4033;
    -webkit-tap-highlight-color: transparent;
    text-rendering: optimizeLegibility;
  }
}

@layer utilities {
  .safe-top {
    padding-top: env(safe-area-inset-top);
  }

  .safe-bottom {
    padding-bottom: env(safe-area-inset-bottom);
  }
}
```

- [ ] **Step 2: 手工检查阻塞项已规避**

Run:

```powershell
Get-Content d:\Fish\src-mobile\style.css
```

Expected: 存在 `viewport-fit=cover` 配套的安全区类；没有 PC 端的 `overflow-hidden` 全局锁死。

- [ ] **Step 3: Commit**

```bash
git add d:/Fish/src-mobile/style.css
git commit -m "style: add mobile safe-area baseline"
```

---

### Task 8: 定义后端兼容增强清单，避免后续返工

**Files:**
- Modify: `d:\Fish\docs\mobile-api-contract.md`
- Test: 文档检查

- [ ] **Step 1: 在文档中追加后端改造顺序**

```md
## Backend Enhancement Order

1. 先把头像和图片上传改成 URL 化，禁止继续新增 Base64 响应。
2. 为移动端增加更轻的列表返回字段集合，但默认接口行为不变。
3. 如果需要离线缓存，新增更新时间戳字段和增量同步参数。
4. 移动端专属接口只能新增，不能替换 PC 端默认接口。
```

- [ ] **Step 2: 检查文档约束是否清晰**

Run:

```powershell
Get-Content d:\Fish\docs\mobile-api-contract.md
```

Expected: 文档明确“先 URL 化图片，再做轻量 payload，再做离线同步”。

- [ ] **Step 3: Commit**

```bash
git add d:/Fish/docs/mobile-api-contract.md
git commit -m "docs: define backend compatibility steps for mobile"
```

---

## Verification Checklist

- `d:\Fish\src` 未被修改
- `d:\Fish\index.html` 未被修改
- `d:\Fish\vite.config.ts` 未被修改
- 移动端能通过 `mobile.html` + `vite.mobile.config.ts` 独立启动
- 移动端登录态 localStorage key 与 PC 端完全隔离
- 移动端先跑通 `登录 -> 首页 -> 品种列表` 三条链路
- 后端默认接口行为未改动

## Notes

- 当前最优先阻塞项不是 UI，而是图片链路。移动端实施前必须把头像和业务图片逐步从 Base64 迁移到 URL。
- `src-mobile` 初期只复制必要页面，不要整份 `src` 机械拷贝，否则会把 PC 的大屏布局和 hover 交互原样带入移动端。
- 如需后续接入真机壳层，优先选择在此隔离结构上接 Capacitor，而不是回改 PC 端入口。

Plan complete and saved to `docs/superpowers/plans/2026-06-08-mobile-frontend-isolation.md`. Two execution options:

1. Subagent-Driven (recommended) - 我按任务逐个派发子代理执行并在每一步回看结果
2. Inline Execution - 我在当前会话里按这个计划直接开始创建移动端独立目录和入口

Which approach?
