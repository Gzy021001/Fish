<template>
  <div
    class="min-h-screen flex items-center justify-center relative overflow-hidden"
    style="
      background:
        linear-gradient(180deg, #fbf7ee 0%, #f7f0e0 15%, #f1e7d2 35%, #ebdfc6 55%, #e6d7bb 75%, #e1d0b0 100%);
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

    <div class="w-full max-w-sm z-10 px-4">
      <div class="bg-white/95 rounded-lg shadow-[0_10px_40px_rgba(74,52,40,0.12)] border border-[#d8c08a]/50 p-10">
        <div class="text-center mb-6">
          <p class="text-lg font-serif font-bold tracking-[0.25em] text-[#4a3428]">
            修改初始密码
          </p>
          <p class="text-xs text-[#8a7659] mt-2">
            首次登录必须修改初始密码后才能继续使用
          </p>
          <div class="w-12 h-px bg-[#c9a96a]/60 mx-auto mt-4"></div>
        </div>

        <form @submit.prevent="handleChangePassword" class="space-y-5">
          <div>
            <label class="block text-xs tracking-wider text-[#7a6850] mb-2">新密码</label>
            <input
              v-model="newPassword"
              type="password"
              required
              minlength="6"
              class="w-full px-4 py-2.5 bg-[#fbf7ee]/70 border border-[#d8c08a]/70 rounded text-[#3a2e22] text-sm placeholder-[#b3a389] outline-none focus:border-[#bfa05f] focus:bg-[#fdfaf2] transition-colors"
              placeholder="至少 6 位"
            />
          </div>

          <div>
            <label class="block text-xs tracking-wider text-[#7a6850] mb-2">确认新密码</label>
            <input
              v-model="confirmPassword"
              type="password"
              required
              class="w-full px-4 py-2.5 bg-[#fbf7ee]/70 border border-[#d8c08a]/70 rounded text-[#3a2e22] text-sm placeholder-[#b3a389] outline-none focus:border-[#bfa05f] focus:bg-[#fdfaf2] transition-colors"
              placeholder="再次输入新密码"
            />
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full py-2.5 rounded text-[#f7efe0] font-serif tracking-[0.18em] text-sm transition-colors flex justify-center items-center disabled:opacity-50 disabled:cursor-not-allowed bg-[#4a3428] hover:bg-[#5a4033]"
          >
            <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            确认修改
          </button>

          <button
            type="button"
            @click="handleLogout"
            class="w-full py-2 rounded text-[#7a6850]/80 text-sm hover:text-[#4a3428] hover:bg-[#f6efe0] transition-colors"
          >
            退出登录
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../api'
import { apiErrorMessage, isAuthError } from '../lib/error'
import { useToast } from '../composables/useToast'

const router = useRouter()
const authStore = useAuthStore()
const toast = useToast()

const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const errorMsg = ref('')

const handleChangePassword = async () => {
  errorMsg.value = ''
  if (newPassword.value.length < 6) {
    errorMsg.value = '新密码至少需要 6 位'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    errorMsg.value = '两次输入的密码不一致'
    return
  }

  loading.value = true
  try {
    await api.post('/change-password', { password: newPassword.value })
    authStore.mustChangePassword = false
    toast.success('密码已修改')
    router.replace('/dashboard')
  } catch (error: any) {
    if (isAuthError(error)) return
    errorMsg.value = apiErrorMessage(error, '修改密码')
  } finally {
    loading.value = false
  }
}

const handleLogout = () => {
  authStore.logout()
  router.replace('/login')
}
</script>
