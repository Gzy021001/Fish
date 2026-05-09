<template>
  <div class="min-h-screen flex items-center justify-center relative overflow-hidden"
    style="
      background:
        linear-gradient(180deg, #fdf8f2 0%, #f8eee0 15%, #f2e4cc 35%, #ece0c4 55%, #e8d8b8 75%, #e5d2ac 100%);
    "
  >
    <Transition name="fade">
      <p
        v-if="errorMsg"
        class="absolute top-6 left-1/2 -translate-x-1/2 z-50 px-5 py-2.5 bg-red-700/90 text-white rounded-lg text-sm shadow-lg backdrop-blur"
      >
        {{ errorMsg }}
      </p>
    </Transition>
    <!-- 穹顶天光 — 模拟石窟顶部开口自然光 -->
    <div class="absolute top-0 left-1/2 -translate-x-1/2 w-[900px] h-[55%] pointer-events-none"
      style="
        background:
          radial-gradient(ellipse at 50% 0%, rgba(255,252,245,0.7) 0%, rgba(255,248,235,0.35) 15%, rgba(232,200,150,0.12) 35%, transparent 60%),
          radial-gradient(ellipse at 50% 0%, rgba(200,160,90,0.2) 0%, transparent 45%);
      "
    ></div>

    <!-- 座下地光 — 大地回光 -->
    <div class="absolute bottom-0 left-0 right-0 h-[35%] pointer-events-none"
      style="
        background:
          radial-gradient(ellipse at 50% 100%, rgba(180,130,70,0.15) 0%, transparent 50%),
          radial-gradient(ellipse at 50% 100%, rgba(210,170,100,0.08) 0%, transparent 35%);
      "
    ></div>

    <!-- 登录卡片 -->
    <div class="w-full max-w-sm z-10 px-4">
      <div class="bg-white rounded-lg shadow-[0_4px_32px_rgba(139,69,19,0.1)] border border-amber-200/50 p-10">

        <!-- 标题 -->
        <div class="text-center mb-8">
          <p class="text-lg font-serif font-bold tracking-[0.25em] text-amber-900">
            鱼类价格后台管理平台
          </p>
          <div class="w-12 h-px bg-amber-300/50 mx-auto mt-4"></div>
        </div>

        <!-- 表单 -->
        <form @submit.prevent="handleLogin" class="space-y-5">
          <div>
            <label class="block text-xs tracking-wider text-amber-800/60 mb-2">用户名</label>
            <input
              v-model="username"
              type="text"
              required
              class="w-full px-4 py-2.5 bg-amber-50/40 border border-amber-200/70 rounded text-amber-900 text-sm placeholder-amber-400/50 outline-none focus:border-amber-400/80 focus:bg-amber-50/80 transition-colors"
              placeholder="请输入用户名"
            />
          </div>

          <div>
            <label class="block text-xs tracking-wider text-amber-800/60 mb-2">密码</label>
            <input
              v-model="password"
              type="password"
              required
              class="w-full px-4 py-2.5 bg-amber-50/40 border border-amber-200/70 rounded text-amber-900 text-sm placeholder-amber-400/50 outline-none focus:border-amber-400/80 focus:bg-amber-50/80 transition-colors"
              placeholder="请输入密码"
            />
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full py-2.5 rounded text-white font-serif tracking-[0.15em] text-sm transition-colors flex justify-center items-center disabled:opacity-50 disabled:cursor-not-allowed"
            style="background: #8b6914;"
          >
            <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            登 录
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'
import { apiErrorMessage } from '../lib/error'

// ============================================================
//  登录页
// ============================================================

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

const username = ref('admin')
const password = ref('admin123')
const loading = ref(false)
const errorMsg = ref('')

const handleLogin = async () => {
  loading.value = true
  errorMsg.value = ''

  try {
    const formData = new URLSearchParams()
    formData.append('username', username.value)
    formData.append('password', password.value)

    const response = await axios.post('http://127.0.0.1:8000/api/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })

    authStore.login(response.data.access_token, username.value)
    router.push('/dashboard')
  } catch (error: any) {
    if (error.response && error.response.status === 404) {
      errorMsg.value = "登录失败：接口未找到 (404)，请确保后端正常运行。"
    } else {
      errorMsg.value = apiErrorMessage(error, "登录")
    }
  } finally {
    loading.value = false
  }
}
</script>
