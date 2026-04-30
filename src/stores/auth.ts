import { defineStore } from 'pinia'
import { ref } from 'vue'

// ============================================================
//  认证状态管理 — Pinia
//  Token 和用户名持久化到 localStorage
// ============================================================

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const username = ref<string | null>(localStorage.getItem('username'))

  /** 登录：保存 token 和用户名 */
  function login(newToken: string, user: string) {
    token.value = newToken
    username.value = user
    localStorage.setItem('token', newToken)
    localStorage.setItem('username', user)
  }

  /** 登出：清除 token 和用户名 */
  function logout() {
    token.value = null
    username.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('username')
  }

  return { token, username, login, logout }
})
