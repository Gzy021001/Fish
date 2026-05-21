import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import router from '../router'

// ============================================================
//  HTTP 请求实例 — Axios
//  所有页面通过 import api from "../api" 统一使用
// ============================================================

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 20000
})

// ---- 请求拦截：自动附加 JWT Token ----
api.interceptors.request.use(config => {
  const authStore = useAuthStore()
  if (authStore.token) {
    config.headers.Authorization = `Bearer ${authStore.token}`
  }
  return config
})

// ---- 响应拦截：401 自动登出跳转 ----
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      router.replace('/login')
      return Promise.reject(error)
    }
    return Promise.reject(error)
  }
)

export default api
