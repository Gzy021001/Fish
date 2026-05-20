import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import router from '../router'

// ============================================================
//  HTTP 请求实例 — Axios
//  所有页面通过 import api from "../api" 统一使用
// ============================================================

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 10000
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

      // 路由跳转比 location.reload 更安全，适配预览环境
      router.replace('/login')

      // 返回永不 resolve 的 Promise，中断业务层 catch 链
      return new Promise(() => {})
    }
    return Promise.reject(error)
  }
)

export default api
