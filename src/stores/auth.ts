import { computed } from 'vue'
import { defineStore } from 'pinia'
import { useStorage } from '@vueuse/core'

export const useAuthStore = defineStore('auth', () => {
  const token = useStorage<string | null>('token', null)
  const username = useStorage<string | null>('username', null)
  const role = useStorage<string | null>('role', null)

  const isAdmin = computed(() => role.value === 'admin')

  function login(newToken: string, user: string, userRole: string) {
    token.value = newToken
    username.value = user
    role.value = userRole
  }

  function logout() {
    token.value = null
    username.value = null
    role.value = null
  }

  return { token, username, role, isAdmin, login, logout }
})
