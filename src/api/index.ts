import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import router from '../router'
import type { ApiError } from '../types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 40000, // 增加到 40s，应对 Neon 数据库的冷启动延迟
})

const RETRYABLE_STATUS = new Set<number>([502, 503])
const RETRY_DELAY_MS = 4000

const _inFlight = new Map<string, AbortController>()

function _reqKey(config: { method?: string; url?: string; params?: unknown }): string {
  return `${config.method ?? 'get'}:${config.url ?? ''}:${JSON.stringify(config.params ?? '')}`
}

function _registerSignal(config: { method?: string; url?: string; signal?: unknown; __inflight_key?: string }) {
  if (config.method !== 'get' || !config.url) return
  const key = _reqKey(config)
  const prev = _inFlight.get(key)
  if (prev) prev.abort()
  const ctrl = new AbortController()
  ;(config as Record<string, unknown>).signal = ctrl.signal
  _inFlight.set(key, ctrl)
  config.__inflight_key = key
}

function _releaseSignal(config: { signal?: unknown; __inflight_key?: string }) {
  if (config.__inflight_key == null) return
  const ctrl = _inFlight.get(config.__inflight_key)
  if (ctrl && (config as Record<string, unknown>).signal === ctrl.signal) _inFlight.delete(config.__inflight_key)
}

function _shouldRetry(error: ApiError): boolean {
  if (!error.config || (error.config as Record<string, unknown>).__retried) return false
  const status = error.response?.status
  if (status != null && RETRYABLE_STATUS.has(status)) return true
  return error.response == null && error.code !== 'ECONNABORTED'
}

api.interceptors.request.use(config => {
  const authStore = useAuthStore()
  if (authStore.token) {
    config.headers.Authorization = `Bearer ${authStore.token}`
  }
  _registerSignal(config as { method?: string; url?: string; signal?: unknown; __inflight_key?: string })
  return config
})

api.interceptors.response.use(
  response => {
    _releaseSignal(response.config as { signal?: unknown; __inflight_key?: string })
    return response
  },
  async (error: ApiError) => {
    _releaseSignal(error.config as { signal?: unknown; __inflight_key?: string })

    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      router.replace('/login')
      return Promise.reject(error)
    }

    if (_shouldRetry(error)) {
      ;(error.config as Record<string, unknown>).__retried = true
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS))
      return api.request(error.config!)
    }

    return Promise.reject(error)
  },
)

export default api
