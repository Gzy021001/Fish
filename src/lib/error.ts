import type { ApiError } from '../types'

export function apiErrorMessage(error: ApiError, context: string): string {
  if (error.response) {
    const data = error.response.data
    const detail = data?.detail
    const serverError = data?.error
    const status = error.response.status

    if (status === 404) return detail || `${context}失败：接口不存在`
    if (status >= 500) {
      const baseMsg = detail || `${context}失败：服务器内部错误`
      let errorInfo = ''

      if (serverError) {
        errorInfo = typeof serverError === 'object' ? JSON.stringify(serverError) : String(serverError)
      } else if (data) {
        errorInfo = JSON.stringify(data)
      }

      return errorInfo ? `${baseMsg} (${errorInfo})` : baseMsg
    }
    if (status === 400) return detail || `${context}失败：请求参数有误`
    if (status === 403) return detail || `${context}失败：无权限访问`
    return detail || `${context}失败（错误码 ${status}）`
  }
  if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
    return `${context}超时，服务器正在唤醒或响应过慢，请稍后重试`
  }
  return `${context}失败：无法连接到服务器，已自动重试。如果问题持续，请稍后刷新页面。`
}

export function isAuthError(error: ApiError): boolean {
  return error.response?.status === 401
}
