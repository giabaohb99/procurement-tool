import { beforeEach, describe, expect, it, vi } from 'vitest'

import { appConfig } from '@/core/config/app-config'
import type { AuthUser, LoginResponse } from './auth-types'

const setTokens = vi.fn()
const clear = vi.fn()

vi.mock('@/core/api', () => ({
  queryClient: { clear: vi.fn() },
  tokenStorage: {
    setTokens: (...args: unknown[]) => setTokens(...args),
    clear: () => clear(),
  },
}))

const login = vi.fn()
const loginGoogle = vi.fn()

vi.mock('./auth-service', () => ({
  authService: {
    login: (...args: unknown[]) => login(...args),
    loginGoogle: (...args: unknown[]) => loginGoogle(...args),
    logout: () => Promise.resolve(null),
  },
}))

const { useAuthStore } = await import('./auth-store')

/** Hồ sơ tối thiểu — store chỉ cất nguyên khối chứ không đọc vào trong. */
const user = { id: 7, username: 'NV007' } as unknown as AuthUser

function session(overrides: Partial<LoginResponse> = {}): LoginResponse {
  return {
    access_token: 'access-1',
    refresh_token: 'refresh-1',
    user,
    ...overrides,
  } as LoginResponse
}

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  useAuthStore.setState({ user: null, isLoggingIn: false })
})

describe('auth store — two login doors (bao-CR-406)', () => {
  it('opens the exact same session for Google as for password', async () => {
    // Bẫy đã lường: chép tay nhánh Google rồi quên một bước (hay gặp nhất là
    // refresh_token) — phiên Google sống tới lúc access token hết hạn rồi đá
    // người dùng ra, mà không chỗ nào đỏ lên.
    login.mockResolvedValue(session())
    await useAuthStore.getState().login({ username: 'NV007', password: 'x' })
    const afterPassword = {
      tokens: setTokens.mock.calls,
      stored: localStorage.getItem(appConfig.storageKeys.user),
      user: useAuthStore.getState().user,
    }

    vi.clearAllMocks()
    localStorage.clear()
    useAuthStore.setState({ user: null })

    loginGoogle.mockResolvedValue(session())
    await useAuthStore.getState().loginGoogle('jwt-cua-google')

    expect(setTokens.mock.calls).toEqual(afterPassword.tokens)
    expect(localStorage.getItem(appConfig.storageKeys.user)).toBe(afterPassword.stored)
    expect(useAuthStore.getState().user).toEqual(afterPassword.user)
  })

  it('passes the Google credential through untouched', async () => {
    // JWT của Google có dấu chấm và ký tự base64url; cắt gọt hay encode thêm là
    // backend xác thực chữ ký hỏng.
    const credential = 'eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxMjMifQ.aGVsbG8td29ybGQ_-'
    loginGoogle.mockResolvedValue(session())
    await useAuthStore.getState().loginGoogle(credential)
    expect(loginGoogle).toHaveBeenCalledWith(credential)
  })

  it('unlocks the submit button when the Google door fails', async () => {
    // Google trả về JWT nhưng backend không tra ra hồ sơ nhân sự -> ném lỗi.
    // Thiếu `finally` thì nút Đăng nhập khóa vĩnh viễn, phải F5 mới nhập lại được.
    loginGoogle.mockRejectedValue(new Error('Email chua gan vao ho so nhan su'))
    await expect(useAuthStore.getState().loginGoogle('jwt')).rejects.toThrow()
    expect(useAuthStore.getState().isLoggingIn).toBe(false)
    expect(useAuthStore.getState().user).toBeNull()
    expect(setTokens).not.toHaveBeenCalled()
    expect(localStorage.getItem(appConfig.storageKeys.user)).toBeNull()
  })
})
