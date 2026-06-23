export function apiErrorMessage(error: any, context: string): string {
  if (error.response) {
    const data = error.response.data
    const detail = data?.detail
    const serverError = data?.error // 后端返回的具体错误描述
    const status = error.response.status
    
    if (status === 404) return detail || `${context}失败：接口不存在`
    if (status >= 500) {
      const baseMsg = detail || `${context}失败：服务器内部错误`
      let errorInfo = ''
      
      if (serverError) {
        errorInfo = typeof serverError === 'object' ? JSON.stringify(serverError) : String(serverError)
      } else if (data && typeof data === 'object') {
        errorInfo = JSON.stringify(data)
      } else if (typeof data === 'string') {
        errorInfo = data.length > 100 ? data.substring(0, 100) + '...' : data
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

export function isAuthError(error: any): boolean {
  return error.response && error.response.status === 401
}
