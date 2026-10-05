import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import type { AuthUser } from '@/core/auth/auth-types'
import { queryKeys } from '@/shared/constants/query-keys'
import type { WorkHistoryFile } from '../types/employee-work-history'

/*  Lỗi phát hiện lúc kiểm tay bằng Chrome DevTools 03/10/2026: mở hộp «Quản lý
    tệp» của một dòng, tải tệp lên thành công (toast báo đúng) nhưng cột «Tệp»
    của dòng ở bảng ngoài vẫn đứng «—» — phải bấm «Tải lại dữ liệu» mới thấy số
    mới. Nguyên nhân: hộp tệp chỉ dọn khóa `workHistoryFiles(historyId)` của
    CHÍNH NÓ, không dọn `employeeWorkHistory(eid)` — khóa mà bảng ngoài đọc
    `file_count` từ đó. */

const uploadMock = vi.fn()
const deleteMock = vi.fn()
const fetchMock = vi.fn()
vi.mock('../api/employee-work-history-api', () => ({
  uploadWorkHistoryFiles: (...args: unknown[]) => uploadMock(...args),
  deleteWorkHistoryFile: (...args: unknown[]) => deleteMock(...args),
  fetchWorkHistoryFiles: (...args: unknown[]) => fetchMock(...args),
}))

const { useDeleteWorkHistoryFile, useUploadWorkHistoryFiles } = await import(
  './use-employee-work-history-files'
)

const HISTORY_ID = 7
const EMPLOYEE_ID = 42
const OTHER_EMPLOYEE_ID = 99

function authUser(employeeId: number): AuthUser {
  return {
    id: 1,
    email: 'a@b.com',
    full_name: 'Người tự xem',
    employee_id: employeeId,
    permissions: {},
  }
}

function file(): WorkHistoryFile {
  return { id: 1, file_id: 1, filename: 'qd.pdf', url: '', content_type: 'application/pdf', size: 100 }
}

let queryClient: QueryClient

function wrapper({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}

beforeEach(() => {
  uploadMock.mockReset()
  deleteMock.mockReset()
  fetchMock.mockReset()
  queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  useAuthStore.setState({ user: null })
  //  Cần một bản cache SẴN CÓ để `invalidateQueries` có chỗ đánh dấu — khóa
  //  chưa từng đọc qua thì không có `QueryState` nào để kiểm `isInvalidated`.
  queryClient.setQueryData(queryKeys.hr.employeeWorkHistory(EMPLOYEE_ID), {
    items: [],
    can_edit: true,
    can_open_files: true,
  })
  queryClient.setQueryData(queryKeys.hr.myWorkHistory(), {
    items: [],
    can_edit: true,
    can_open_files: true,
  })
  queryClient.setQueryData(queryKeys.hr.workHistoryFiles(HISTORY_ID), [])
})

describe('useUploadWorkHistoryFiles — dọn cache của BẢNG NGOÀI sau khi tải tệp', () => {
  it('tải tệp thành công → dọn luôn employeeWorkHistory(eid), không chỉ workHistoryFiles của hộp', async () => {
    uploadMock.mockResolvedValue([file()])
    useAuthStore.setState({ user: authUser(OTHER_EMPLOYEE_ID) }) // người xem KHÁC chủ hồ sơ

    const { result } = renderHook(() => useUploadWorkHistoryFiles(HISTORY_ID, EMPLOYEE_ID), { wrapper })
    await act(async () => {
      await result.current.mutateAsync([new File(['x'], 'qd.pdf')])
    })

    expect(
      queryClient.getQueryState(queryKeys.hr.employeeWorkHistory(EMPLOYEE_ID))?.isInvalidated,
    ).toBe(true)
    expect(
      queryClient.getQueryState(queryKeys.hr.workHistoryFiles(HISTORY_ID))?.isInvalidated,
    ).toBe(true)
  })

  it('tải tệp vào dòng của CHÍNH MÌNH → dọn thêm myWorkHistory (Trang cá nhân đọc file_count ở đó)', async () => {
    uploadMock.mockResolvedValue([file()])
    useAuthStore.setState({ user: authUser(EMPLOYEE_ID) })

    const { result } = renderHook(() => useUploadWorkHistoryFiles(HISTORY_ID, EMPLOYEE_ID), { wrapper })
    await act(async () => {
      await result.current.mutateAsync([new File(['x'], 'qd.pdf')])
    })

    expect(queryClient.getQueryState(queryKeys.hr.myWorkHistory())?.isInvalidated).toBe(true)
  })

  it('tải tệp vào dòng của NGƯỜI KHÁC → KHÔNG dọn myWorkHistory của người đang xem', async () => {
    uploadMock.mockResolvedValue([file()])
    useAuthStore.setState({ user: authUser(OTHER_EMPLOYEE_ID) })

    const { result } = renderHook(() => useUploadWorkHistoryFiles(HISTORY_ID, EMPLOYEE_ID), { wrapper })
    await act(async () => {
      await result.current.mutateAsync([new File(['x'], 'qd.pdf')])
    })

    expect(queryClient.getQueryState(queryKeys.hr.myWorkHistory())?.isInvalidated).not.toBe(true)
  })
})

describe('useDeleteWorkHistoryFile — cùng luật dọn cache với upload', () => {
  it('gỡ tệp thành công → dọn employeeWorkHistory(eid) của dòng đó', async () => {
    deleteMock.mockResolvedValue(null)
    useAuthStore.setState({ user: authUser(OTHER_EMPLOYEE_ID) })

    const { result } = renderHook(() => useDeleteWorkHistoryFile(HISTORY_ID, EMPLOYEE_ID), { wrapper })
    await act(async () => {
      await result.current.mutateAsync(1)
    })

    expect(
      queryClient.getQueryState(queryKeys.hr.employeeWorkHistory(EMPLOYEE_ID))?.isInvalidated,
    ).toBe(true)
  })
})
