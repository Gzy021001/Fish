import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import router from '../router'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 20000,
})

const RETRYABLE_STATUS = new Set<number>([502, 503])
const RETRY_DELAY_MS = 4000

const _inFlight = new Map<string, AbortController>()

function _reqKey(config: { method?: string; url?: string; params?: any }): string {
  return `${config.method ?? 'get'}:${config.url ?? ''}:${JSON.stringify(config.params ?? '')}`
}

function _registerSignal(config: any) {
  if (config.method !== 'get' || !config.url) return
  const key = _reqKey(config)
  const prev = _inFlight.get(key)
  if (prev) prev.abort()
  const ctrl = new AbortController()
  config.signal = ctrl.signal
  _inFlight.set(key, ctrl)
  ;(config as any).__inflight_key = key
}

function _releaseSignal(config: any) {
  if ((config as any)?.__inflight_key == null) return
  const key = (config as any).__inflight_key as string
  const ctrl = _inFlight.get(key)
  if (ctrl?.signal === config.signal) _inFlight.delete(key)
}

function _shouldRetry(error: any): boolean {
  if (!error.config || error.config.__retried) return false
  const status = error.response?.status
  if (status != null && RETRYABLE_STATUS.has(status)) return true
  return error.response == null && error.code !== 'ECONNABORTED'
}

api.interceptors.request.use(config => {
  const authStore = useAuthStore()
  if (authStore.token) {
    config.headers.Authorization = `Bearer ${authStore.token}`
  }
  _registerSignal(config)
  return config
})

api.interceptors.response.use(
  response => {
    _releaseSignal(response.config)
    return response
  },
  async error => {
    _releaseSignal(error.config)

    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      router.replace('/login')
      return Promise.reject(error)
    }

    if (_shouldRetry(error)) {
      error.config.__retried = true
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS))
      return api.request(error.config)
    }

    return Promise.reject(error)
  },
)

export default api
