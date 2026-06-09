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
