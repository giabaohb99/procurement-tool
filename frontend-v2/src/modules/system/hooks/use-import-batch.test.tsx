import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useCommitImport, useImportBatch, useImportLogs, useRevertImport } from './use-imports'

const get = vi.fn()
const logs = vi.fn()
const revert = vi.fn()
const commit = vi.fn()
const toastError = vi.fn()

vi.mock('sonner', () => ({
  toast: { error: (...a: unknown[]) => toastError(...a), success: vi.fn() },
}))

vi.mock('../api/import-api', () => ({
  importApi: {
    get: (...a: unknown[]) => get(...a),
    logs: (...a: unknown[]) => logs(...a),
    revert: (...a: unknown[]) => revert(...a),
    commit: (...a: unknown[]) => commit(...a),
  },
}))

function setup() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
  return { queryClient, wrapper }
}

beforeEach(() => {
  get.mockReset()
  logs.mockReset()
  revert.mockReset()
  commit.mockReset()
  toastError.mockReset()
})

describe('useImportBatch', () => {
  it('lô chuyển từ Đang chạy sang Xong thì tải lại nhật ký (không cần F5)', async () => {
    logs.mockResolvedValueOnce({ total: 0, items: [] })
    logs.mockResolvedValue({ total: 1, items: [{ id: 1 }] })
    get.mockResolvedValueOnce({ id: 7, status: 1 }) // Đang chạy
    const { queryClient, wrapper } = setup()

    const { result } = renderHook(
      () => ({ batch: useImportBatch(7), logs: useImportLogs(7, {}) }),
      { wrapper },
    )
    await waitFor(() => expect(result.current.logs.data?.total).toBe(0))
    expect(logs).toHaveBeenCalledTimes(1)

    // Worker xong: lần đọc kế tiếp của lô trả Xong.
    get.mockResolvedValue({ id: 7, status: 2 })
    await act(async () => {
      await queryClient.invalidateQueries({ queryKey: ['system', 'imports', 'detail', 7] })
    })
    await waitFor(() => expect(result.current.logs.data?.total).toBe(1))
    expect(logs.mock.calls.length).toBeGreaterThanOrEqual(2)
  })

  it('lô đã Xong ngay từ đầu thì không tải nhật ký thêm', async () => {
    logs.mockResolvedValue({ total: 2, items: [] })
    get.mockResolvedValue({ id: 8, status: 2 })
    const { wrapper } = setup()
    const { result } = renderHook(
      () => ({ batch: useImportBatch(8), logs: useImportLogs(8, {}) }),
      { wrapper },
    )
    await waitFor(() => expect(result.current.logs.data?.total).toBe(2))
    await waitFor(() => expect(result.current.batch.data?.status).toBe(2))
    expect(logs).toHaveBeenCalledTimes(1)
  })
})

describe('toast lỗi hoàn tác / ghi thật', () => {
  //  `httpClient` đã toast mọi lỗi POST; hook thêm lần nữa là người dùng thấy HAI toast.
  it('hoàn tác bị từ chối: hook KHÔNG tự toast thêm', async () => {
    revert.mockRejectedValue(new Error('Không hoàn tác được MOI01'))
    const { wrapper } = setup()
    const { result } = renderHook(() => useRevertImport(), { wrapper })
    await act(async () => {
      await result.current.mutateAsync(7).catch(() => undefined)
    })
    expect(toastError).not.toHaveBeenCalled()
  })

  it('ghi thật bị từ chối: hook KHÔNG tự toast thêm', async () => {
    commit.mockRejectedValue(new Error('đã ghi thật'))
    const { wrapper } = setup()
    const { result } = renderHook(() => useCommitImport(), { wrapper })
    await act(async () => {
      await result.current.mutateAsync(7).catch(() => undefined)
    })
    expect(toastError).not.toHaveBeenCalled()
  })
})

describe('useImportBatch đổi lô', () => {
  it('đổi id: trạng thái "đang chạy" của lô trước không kích hoạt tải nhật ký lô sau', async () => {
    logs.mockResolvedValue({ total: 0, items: [] })
    get.mockImplementation((id: number) =>
      Promise.resolve({ id, status: id === 1 ? 1 : 2 }),
    )
    const { wrapper } = setup()
    const { result, rerender } = renderHook(
      ({ id }: { id: number }) => ({ batch: useImportBatch(id), logs: useImportLogs(id, {}) }),
      { wrapper, initialProps: { id: 1 } },
    )
    await waitFor(() => expect(result.current.batch.data?.status).toBe(1))
    rerender({ id: 2 })
    await waitFor(() => expect(result.current.batch.data?.id).toBe(2))
    await waitFor(() => expect(result.current.logs.data).toBeDefined())
    const callsForSecond = logs.mock.calls.filter((c) => c[0] === 2).length
    expect(callsForSecond).toBe(1)
  })
})
