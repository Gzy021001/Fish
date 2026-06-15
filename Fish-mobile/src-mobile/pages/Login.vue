<template>
  <div
    class="min-h-screen flex items-center justify-center px-5 py-8"
    style="background: linear-gradient(180deg, #fdf8f2 0%, #f2e4cc 45%, #e5d2ac 100%);"
  >
    <form
      class="w-full max-w-sm space-y-4 rounded-2xl bg-white/90 p-5 shadow-lg backdrop-blur"
      @submit.prevent="handleLogin"
    >
      <h1 class="text-xl font-serif text-center text-[#6d4f32]">移动端登录</h1>

      <input
        v-model="username"
        class="w-full rounded-xl border border-[#d8c1a0] bg-white px-4 py-3 text-[#5c4033] outline-none"
        placeholder="用户名"
      />

      <input
        v-model="password"
        type="password"
        class="w-full rounded-xl border border-[#d8c1a0] bg-white px-4 py-3 text-[#5c4033] outline-none"
        placeholder="密码"
      />

      <button
        :disabled="loading"
        class="w-full rounded-xl bg-[#8b6914] py-3 text-white disabled:opacity-60"
      >
        {{ loading ? '登录中...' : '登录' }}
      </button>

      <p v-if="errorMsg" class="text-sm text-red-600">{{ errorMsg }}</p>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { useAuthStore } from '../stores/auth'
import { apiErrorMessage } from '../../src/lib/error'

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

    const response = await api.post('/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })

    authStore.login(response.data.access_token, username.value)
    router.push('/dashboard')
  } catch (error: any) {
    errorMsg.value = apiErrorMessage(error, '登录')
  } finally {
    loading.value = false
  }
}
</script>
