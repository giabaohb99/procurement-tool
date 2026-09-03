import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { queryKeys } from '@/shared/constants/query-keys'

/*  Cùng lớp lỗi bao-CR-276 với hook ghim: quản trị viên ẩn/gỡ một thread ngay
    trên trang thread của box thì danh sách vẫn hiện bài tới khi F5 — hook bỏ
    quên nhánh `boards` (và chiều ngược lại: khôi phục xong bài không hiện lại).  */

const hideMock = vi.fn()
const removeMock = vi.fn()
const restoreMock = vi.fn()
vi.mock('../api/forum-api', () => ({
  hideForumPost: (id: number, reason: string) => hideMock(id, reason),
  removeForumPost: (id: number, reason: string) => removeMock(id, reason),
  restoreForumPost: (id: number) => restoreMock(id),
}))

const { useModerateForumPost } = await import('./use-moderate-forum-post')

let queryClient: QueryClient

function wrapper({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}

function threadPageState() {
  return queryClient.getQueryState(queryKeys.forum.boardThreads(5, 1))
}

beforeEach(() => {
  for (const mock of [hideMock, removeMock, restoreMock]) {
    mock.mockReset()
    mock.mockResolvedValue(null)
  }
  queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  queryClient.setQueryData(queryKeys.forum.boardThreads(5, 1), { items: [], total: 1 })
})

describe('useModerateForumPost', () => {
  it('hiding a thread invalidates the box thread pages so it disappears without a reload', async () => {
    const { result } = renderHook(() => useModerateForumPost(), { wrapper })
    await act(async () => {
      result.current.mutate({ postId: 40, action: 'hide', reason: 'spam' })
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(hideMock).toHaveBeenCalledWith(40, 'spam')
    expect(threadPageState()?.isInvalidated).toBe(true)
  })

  it('restoring goes through the same sweep — the thread has to COME BACK to the list', async () => {
    const { result } = renderHook(() => useModerateForumPost(), { wrapper })
    await act(async () => {
      result.current.mutate({ postId: 40, action: 'restore' })
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(restoreMock).toHaveBeenCalledWith(40)
    expect(threadPageState()?.isInvalidated).toBe(true)
  })

  it('removing sweeps the boards branch too', async () => {
    const { result } = renderHook(() => useModerateForumPost(), { wrapper })
    await act(async () => {
      result.current.mutate({ postId: 40, action: 'remove', reason: 'vi phạm' })
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(removeMock).toHaveBeenCalledWith(40, 'vi phạm')
    expect(threadPageState()?.isInvalidated).toBe(true)
  })
})
