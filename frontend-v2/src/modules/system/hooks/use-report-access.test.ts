import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { createElement, type ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { AuthUser } from '@/core/auth/auth-types'
import { reportAccessApi } from '../api/report-access-api'
import { useGrantReportAccess, useRevokeReportAccess } from './use-report-access'

//  M2 (rà soát tính năng phân quyền từng báo cáo): `report_keys` quyết định
//  menu nằm trong store zustand, không trong cache React Query —
//  `invalidateQueries(auth.me())` một mình không kéo được `useAuthStore`.
//  Phải gọi thẳng `authService.me()` rồi `useAuthStore.getState().setUser(...)`.
const meMock = vi.fn()
vi.mock('@/core/auth/auth-service', () => ({
  authService: { me: (...args: unknown[]) => meMock(...args) },
}))

const setUser = vi.fn()
vi.mock('@/core/auth/auth-store', () => ({
  useAuthStore: { getState: () => ({ setUser }) },
}))

vi.mock('../api/report-access-api', () => ({
  reportAccessApi: { grant: vi.fn(), revoke: vi.fn() },
}))

const toastSuccess = vi.fn()
const toastWarning = vi.fn()
vi.mock('sonner', () => ({ toast: { success: (...a: unknown[]) => toastSuccess(...a), warning: (...a: unknown[]) => toastWarning(...a) } }))

function freshUser(overrides: Partial<AuthUser> = {}): AuthUser {
  return {
    id: 1,
    email: 'a@dego.vn',
    full_name: 'Người A',
    permissions: {},
    report_keys: [1, 2, 3],
    ...overrides,
  } as AuthUser
}

let queryClient: QueryClient
function wrapper({ children }: { children: ReactNode }) {
  return createElement(QueryClientProvider, { client: queryClient }, children)
}

beforeEach(() => {
  queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  vi.clearAllMocks()
})

describe('useGrantReportAccess — nạp lại hồ sơ CHÍNH MÌNH sau khi gán (M2)', () => {
  it('gán thành công → gọi /auth/me rồi ghi NGAY vào store (menu đổi tại chỗ)', async () => {
    vi.mocked(reportAccessApi.grant).mockResolvedValue({ created: 1, updated: 0, skipped: [] })
    const freshProfile = freshUser({ report_keys: [1, 2, 3, 9] })
    meMock.mockResolvedValue(freshProfile)

    const { result } = renderHook(() => useGrantReportAccess(9), { wrapper })
    result.current.mutate({ subjects: [{ subject_kind: 1, subject_id: 1 }], effect: 1 })

    await waitFor(() => expect(setUser).toHaveBeenCalledWith(freshProfile))
    expect(meMock).toHaveBeenCalledTimes(1)
    expect(toastSuccess).toHaveBeenCalled()
  })

  it('/auth/me lỗi sau khi gán → NUỐT ÂM THẦM, toast thành công của việc gán vẫn hiện', async () => {
    vi.mocked(reportAccessApi.grant).mockResolvedValue({ created: 1, updated: 0, skipped: [] })
    meMock.mockRejectedValue(new Error('mạng lỗi'))

    const { result } = renderHook(() => useGrantReportAccess(9), { wrapper })
    result.current.mutate({ subjects: [{ subject_kind: 1, subject_id: 1 }], effect: 1 })

    await waitFor(() => expect(toastSuccess).toHaveBeenCalled())
    //  Lỗi nạp lại hồ sơ không được ném ra ngoài — nếu nó ném, test này treo/đỏ
    //  vì `useMutation` sẽ không coi đây là `onSuccess` của MUTATION gán (mutate
    //  vẫn thành công, chỉ việc nạp lại hồ sơ là việc PHỤ chạy sau).
    expect(setUser).not.toHaveBeenCalled()
  })
})

describe('useRevokeReportAccess — nạp lại hồ sơ CHÍNH MÌNH sau khi thu hồi (M2)', () => {
  it('thu hồi thành công → gọi /auth/me rồi ghi vào store', async () => {
    vi.mocked(reportAccessApi.revoke).mockResolvedValue(undefined)
    const freshProfile = freshUser({ report_keys: [] })
    meMock.mockResolvedValue(freshProfile)

    const { result } = renderHook(() => useRevokeReportAccess(), { wrapper })
    result.current.mutate({ accessId: 42, reason: '' })

    await waitFor(() => expect(setUser).toHaveBeenCalledWith(freshProfile))
    expect(toastSuccess).toHaveBeenCalled()
  })

  it('/auth/me lỗi sau khi thu hồi → NUỐT ÂM THẦM, không chặn toast thu hồi', async () => {
    vi.mocked(reportAccessApi.revoke).mockResolvedValue(undefined)
    meMock.mockRejectedValue(new Error('mạng lỗi'))

    const { result } = renderHook(() => useRevokeReportAccess(), { wrapper })
    result.current.mutate({ accessId: 42, reason: '' })

    await waitFor(() => expect(toastSuccess).toHaveBeenCalled())
    expect(setUser).not.toHaveBeenCalled()
  })
})
