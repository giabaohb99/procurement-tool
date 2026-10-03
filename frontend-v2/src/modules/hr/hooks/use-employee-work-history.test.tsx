import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import type { AuthUser } from '@/core/auth/auth-types'
import { queryKeys } from '@/shared/constants/query-keys'
import type { EmployeeWorkHistorySaveResult } from '../types/employee-work-history'

/*  Low FE (code review 03/10/2026): áp thay đổi lên hồ sơ CHÍNH MÌNH (quản trị
    hệ thống tự sửa, A9/Q3 cho phép ngoại lệ này) phải làm mới CẢ thẻ «Quá trình
    công tác» ở Trang cá nhân (`myWorkHistory`) LẪN thông tin tài khoản đang
    đăng nhập (`/api/auth/me`) — không thì sidebar/avatar vẫn hiện chức vụ/phòng
    ban CŨ cho tới lần đăng nhập sau. */

const createMock = vi.fn()
const updateMock = vi.fn()
const applyMock = vi.fn()
vi.mock('../api/employee-work-history-api', () => ({
  employeeWorkHistoryApi: {
    create: (...args: unknown[]) => createMock(...args),
    update: (...args: unknown[]) => updateMock(...args),
    apply: (...args: unknown[]) => applyMock(...args),
  },
}))

const meMock = vi.fn()
vi.mock('@/core/auth/auth-service', () => ({
  authService: { me: (...args: unknown[]) => meMock(...args) },
}))

const { useApplyEmployeeWorkHistory, useSaveEmployeeWorkHistory } = await import(
  './use-employee-work-history'
)

const EMPLOYEE_ID = 42
const SELF_ID = 99

function authUser(employeeId: number): AuthUser {
  return {
    id: 1,
    email: 'a@b.com',
    full_name: 'Người tự xem',
    employee_id: employeeId,
    permissions: {},
  }
}

function saveResult(appliedChanges: string[]): EmployeeWorkHistorySaveResult {
  return {
    item: {
      id: 1,
      employee_id: EMPLOYEE_ID,
      event_type: 3,
      from_date: '2026-10-01',
      to_date: null,
      company_id: 0,
      company_name: '',
      department_id: 0,
      department_name: '',
      position_id: 0,
      position_label: '',
      decision_no: '',
      decision_date: null,
      note: '',
      applied_at: appliedChanges.length > 0 ? '2026-10-01' : null,
      file_count: 0,
      is_current: true,
      can_apply: false,
    },
    warnings: [],
    applied_changes: appliedChanges,
  }
}

let queryClient: QueryClient

function wrapper({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}

beforeEach(() => {
  createMock.mockReset()
  updateMock.mockReset()
  applyMock.mockReset()
  meMock.mockReset()
  queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  useAuthStore.setState({ user: null })
})

describe('useSaveEmployeeWorkHistory — làm mới hồ sơ CHÍNH MÌNH sau khi áp (Low FE)', () => {
  it('áp vào hồ sơ CỦA CHÍNH người đang đăng nhập → nạp lại myWorkHistory + gọi /auth/me + cập nhật store', async () => {
    useAuthStore.setState({ user: authUser(EMPLOYEE_ID) })
    createMock.mockResolvedValue(saveResult(['Chức vụ']))
    meMock.mockResolvedValue(authUser(EMPLOYEE_ID))
    //  Cần một bản cache SẴN CÓ để `invalidateQueries` có chỗ đánh dấu —
    //  khóa chưa từng đọc qua thì không có `QueryState` nào để kiểm.
    queryClient.setQueryData(queryKeys.hr.myWorkHistory(), { items: [], can_edit: true, can_open_files: true })

    const { result } = renderHook(() => useSaveEmployeeWorkHistory(EMPLOYEE_ID), { wrapper })
    await act(async () => {
      await result.current.mutateAsync({ payload: {} as never })
    })

    await waitFor(() => expect(meMock).toHaveBeenCalledTimes(1))
    expect(
      queryClient.getQueryState(queryKeys.hr.myWorkHistory())?.isInvalidated,
    ).toBe(true)
    await waitFor(() => expect(useAuthStore.getState().user).toEqual(authUser(EMPLOYEE_ID)))
  })

  it('áp vào hồ sơ CỦA NGƯỜI KHÁC (không phải chính mình) → KHÔNG gọi /auth/me, KHÔNG nạp lại myWorkHistory', async () => {
    useAuthStore.setState({ user: authUser(SELF_ID) }) // khác EMPLOYEE_ID
    createMock.mockResolvedValue(saveResult(['Chức vụ']))

    const { result } = renderHook(() => useSaveEmployeeWorkHistory(EMPLOYEE_ID), { wrapper })
    await act(async () => {
      await result.current.mutateAsync({ payload: {} as never })
    })

    expect(meMock).not.toHaveBeenCalled()
    expect(queryClient.getQueryState(queryKeys.hr.myWorkHistory())?.isInvalidated).not.toBe(true)
  })

  it('LƯU dòng mà KHÔNG áp vào hồ sơ (applied_changes rỗng) → không nạp lại myWorkHistory dù đúng là chính mình', async () => {
    useAuthStore.setState({ user: authUser(EMPLOYEE_ID) })
    createMock.mockResolvedValue(saveResult([]))

    const { result } = renderHook(() => useSaveEmployeeWorkHistory(EMPLOYEE_ID), { wrapper })
    await act(async () => {
      await result.current.mutateAsync({ payload: {} as never })
    })

    expect(meMock).not.toHaveBeenCalled()
    expect(queryClient.getQueryState(queryKeys.hr.myWorkHistory())?.isInvalidated).not.toBe(true)
  })
})

describe('useApplyEmployeeWorkHistory — cùng luật làm mới hồ sơ chính mình', () => {
  it('bấm ▶ áp dòng có sẵn vào hồ sơ CHÍNH MÌNH → nạp lại myWorkHistory + gọi /auth/me', async () => {
    useAuthStore.setState({ user: authUser(EMPLOYEE_ID) })
    applyMock.mockResolvedValue({ item: saveResult(['Chức vụ']).item, applied_changes: ['Chức vụ'] })
    meMock.mockResolvedValue(authUser(EMPLOYEE_ID))
    queryClient.setQueryData(queryKeys.hr.myWorkHistory(), { items: [], can_edit: true, can_open_files: true })

    const { result } = renderHook(() => useApplyEmployeeWorkHistory(EMPLOYEE_ID), { wrapper })
    await act(async () => {
      await result.current.mutateAsync(1)
    })

    await waitFor(() => expect(meMock).toHaveBeenCalledTimes(1))
    expect(queryClient.getQueryState(queryKeys.hr.myWorkHistory())?.isInvalidated).toBe(true)
  })
})
