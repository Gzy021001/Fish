import { describe, it, expect } from 'vitest'
import { apiErrorMessage, isAuthError } from '../src/lib/error'
import type { ApiError } from '../src/types'

describe('apiErrorMessage', () => {
  it('returns 503 base message when detail present', () => {
    const error: ApiError = {
      response: { status: 503, data: { detail: '服务不可用' } },
    }
    const msg = apiErrorMessage(error, '保存')
    expect(msg).toContain('服务不可用')
  })

  it('returns 503 with context when no detail', () => {
    const error: ApiError = {
      response: { status: 503, data: {} },
    }
    const msg = apiErrorMessage(error, '保存')
    expect(msg).toContain('保存失败')
  })

  it('returns 404 message', () => {
    const error: ApiError = {
      response: { status: 404, data: { detail: '资源不存在' } },
    }
    expect(apiErrorMessage(error, '查询')).toBe('资源不存在')
  })

  it('returns timeout message', () => {
    const error: ApiError = { code: 'ECONNABORTED' }
    expect(apiErrorMessage(error, '保存')).toContain('超时')
  })

  it('returns connection error message when no response', () => {
    const error: ApiError = { code: 'ERR_NETWORK' }
    expect(apiErrorMessage(error, '查询')).toContain('无法连接')
  })
})

describe('isAuthError', () => {
  it('returns true for 401 status', () => {
    expect(isAuthError({ response: { status: 401 } })).toBe(true)
  })

  it('returns false for non-401 status', () => {
    expect(isAuthError({ response: { status: 500 } })).toBe(false)
  })

  it('returns false without response', () => {
    expect(isAuthError({ code: 'ERR_NETWORK' })).toBe(false)
  })
})
