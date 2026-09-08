import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { queryKeys } from '@/shared/constants/query-keys'

/*  Cùng lớp lỗi bao-CR-276 với hook ghim: xóa thread trong box xong quay về
    danh sách thread thì bài vẫn đứng đó tới khi F5 — hook chỉ reset feed/tủ
    cá nhân/dải ghim, bỏ quên nhánh `boards`.  */

const deleteMock = vi.fn()
vi.mock('../api/forum-api', () => ({
  deleteForumPost: (id: number) => deleteMock(id),
}))

const { useDeleteForumPost } = await import('./use-delete-forum-post')

let queryClient: QueryClient

function wrapper({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}

beforeEach(() => {
  deleteMock.mockReset()
  deleteMock.mockResolvedValue(null)
  queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
})

describe('useDeleteForumPost', () => {
  it('invalidates the boards branch so the deleted thread leaves the box list without a reload', async () => {
    //  API xóa trả null (không có board_id) nên hook phải quét GỐC boards —
    //  cây chuyên mục lẫn mọi trang thread đều phải nạp lại.
    queryClient.setQueryData(queryKeys.forum.boardThreads(5, 1), { items: [], total: 1 })
    queryClient.setQueryData(queryKeys.forum.boards(), [])

    const { result } = renderHook(() => useDeleteForumPost(), { wrapper })
    await act(async () => {
      result.current.mutate(40)
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(deleteMock).toHaveBeenCalledWith(40)
    expect(queryClient.getQueryState(queryKeys.forum.boardThreads(5, 1))?.isInvalidated).toBe(
      true,
    )
  })

  it('still refreshes the pinned strip — a pinned post the author deletes must leave it', async () => {
    queryClient.setQueryData(queryKeys.forum.pinned(), [])

    const { result } = renderHook(() => useDeleteForumPost(), { wrapper })
    await act(async () => {
      result.current.mutate(40)
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(queryClient.getQueryState(queryKeys.forum.pinned())?.isInvalidated).toBe(true)
  })
})
