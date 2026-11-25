import type { ApiError } from '../types'

/** 统一把接口错误压成一句短提示：优先用后端 detail，其它情况给固定短语 */
export function apiErrorMessage(error: ApiError, context: string): string {
  if (error.response) {
    const detail = error.response.data?.detail
    const status = error.response.status

    if (detail) return String(detail)
    if (status === 404) return `${context}失败：接口不存在`
    if (status >= 500) return `${context}失败：服务异常`
    if (status === 400) return `${context}失败：参数有误`
    if (status === 403) return `${context}失败：无权限`
    return `${context}失败（${status}）`
  }
  if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
    return `${context}超时，请重试`
  }
  return `${context}失败：连接异常，请重试`
}

export function isAuthError(error: ApiError): boolean {
  return error.response?.status === 401
}
