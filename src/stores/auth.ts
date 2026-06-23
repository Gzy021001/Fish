import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const username = ref<string | null>(localStorage.getItem('username'))
  const role = ref<string | null>(localStorage.getItem('role'))

  const isAdmin = computed(() => role.value === 'admin')

  function login(newToken: string, user: string, userRole: string) {
    token.value = newToken
    username.value = user
    role.value = userRole
    localStorage.setItem('token', newToken)
    localStorage.setItem('username', user)
    localStorage.setItem('role', userRole)
  }

  function logout() {
    token.value = null
    username.value = null
    role.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('role')
  }

  return { token, username, role, isAdmin, login, logout }
})
