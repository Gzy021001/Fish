export function apiErrorMessage(error: any, context: string): string {
  if (error.response) {
    const detail = error.response.data?.detail
    const serverError = error.response.data?.error // 后端返回的具体错误描述
    const status = error.response.status
    
    if (status === 404) return detail || `${context}失败：接口不存在`
    if (status >= 500) {
      const baseMsg = detail || `${context}失败：服务器内部错误`
      return serverError ? `${baseMsg} (${serverError})` : baseMsg
    }
    if (status === 400) return detail || `${context}失败：请求参数有误`
    if (status === 403) return detail || `${context}失败：无权限访问`
    return detail || `${context}失败（错误码 ${status}）`
  }
  if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
    return `${context}超时，服务器正在唤醒或响应过慢，请稍后重试`
  }
  return `${context}失败：无法连接到服务器。如果这是部署后首次访问，请稍等 10-20 秒待后端冷启动完成。`
}

export function isAuthError(error: any): boolean {
  return error.response && error.response.status === 401
}
