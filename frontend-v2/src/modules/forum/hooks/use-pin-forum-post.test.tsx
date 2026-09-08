import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { queryKeys } from '@/shared/constants/query-keys'
import type { ForumPost } from '../types/forum-post'

/*  Lỗi QA 03/09 mà tệp này khóa lại: ghim thread trong trang chi tiết box rồi
    bấm quay về danh sách thread thì bài KHÔNG nổi lên đầu, cũng không có icon
    ghim — phải F5 mới thấy. Hook chỉ vá cache feed/tủ cá nhân/dải ghim mà bỏ
    quên nhánh `boards` (trang thread phân trang số trang nằm dưới gốc đó).  */

const pinMock = vi.fn()
const unpinMock = vi.fn()
vi.mock('../api/forum-api', () => ({
  pinForumPost: (id: number) => pinMock(id),
  unpinForumPost: (id: number) => unpinMock(id),
  // `patch-post-caches` import hàm này (chỉ dùng ở nhánh refresh) — vẫn phải khai.
  fetchForumPost: vi.fn(),
}))

const { usePinForumPost } = await import('./use-pin-forum-post')

const BOARD_ID = 5

function makePost(over: Partial<ForumPost> & { id: number }): ForumPost {
  return {
    body: 'Kế hoạch khám sức khỏe định kỳ năm 2026',
    body_format: 0,
    status: 1,
    audience: 3,
    kind: 0,
    dept_id: null,
    company_id: null,
    author_id: 31,
    author_name: 'Nguyễn Kỳ Thảo Thơ',
    author_code: 'TESTREQ',
    author_avatar: '',
    created_at: '2026-09-03 10:00:00',
    board_id: BOARD_ID,
    title: 'Kế hoạch khám sức khỏe định kỳ năm 2026',
    prefix: 0,
    board_name: 'Thông báo công ty',
    pinned_at: '2026-09-03 10:05:00',
    can_delete: false,
    can_moderate: true,
    hidden_reason: '',
    like_count: 0,
    liked: false,
    my_reaction: 0,
    reactions: {},
    comment_count: 0,
    images: [],
    ...over,
  } as ForumPost
}

let queryClient: QueryClient

function wrapper({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}

beforeEach(() => {
  pinMock.mockReset()
  unpinMock.mockReset()
  queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
})

describe('usePinForumPost', () => {
  it('invalidates the cached board thread pages so the pin shows without a reload', async () => {
    const fresh = makePost({ id: 40 })
    pinMock.mockResolvedValue(fresh)
    //  Trang thread đang cache còn bản CHƯA ghim — đúng cảnh người dùng vừa rời.
    queryClient.setQueryData(queryKeys.forum.boardThreads(BOARD_ID, 1), {
      items: [makePost({ id: 40, pinned_at: null })],
      total: 1,
    })

    const { result } = renderHook(() => usePinForumPost(), { wrapper })
    await act(async () => {
      result.current.mutate({ postId: 40, pinned: true })
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    //  Ghim ĐẢO THỨ TỰ trang thread (bài ghim nổi lên đầu) nên phải nạp lại từ
    //  máy chủ, vá tại chỗ không đủ.
    const state = queryClient.getQueryState(queryKeys.forum.boardThreads(BOARD_ID, 1))
    expect(state?.isInvalidated).toBe(true)
  })

  it('also refetches on UNPIN — the thread has to drop back to its date slot', async () => {
    pinMock.mockResolvedValue(undefined)
    unpinMock.mockResolvedValue(makePost({ id: 40, pinned_at: null }))
    queryClient.setQueryData(queryKeys.forum.boardThreads(BOARD_ID, 1), {
      items: [makePost({ id: 40 })],
      total: 1,
    })

    const { result } = renderHook(() => usePinForumPost(), { wrapper })
    await act(async () => {
      result.current.mutate({ postId: 40, pinned: false })
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(unpinMock).toHaveBeenCalledWith(40)
    const state = queryClient.getQueryState(queryKeys.forum.boardThreads(BOARD_ID, 1))
    expect(state?.isInvalidated).toBe(true)
  })

  it('leaves the boards branch alone for a plain feed post (board_id = 0)', async () => {
    pinMock.mockResolvedValue(makePost({ id: 12, board_id: 0, title: '', board_name: '' }))
    queryClient.setQueryData(queryKeys.forum.boardThreads(BOARD_ID, 1), {
      items: [makePost({ id: 40 })],
      total: 1,
    })

    const { result } = renderHook(() => usePinForumPost(), { wrapper })
    await act(async () => {
      result.current.mutate({ postId: 12, pinned: true })
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    //  Bài Bảng tin thuần không đứng trong box nào — quét nhánh boards ở đây
    //  chỉ tốn lượt gọi lại vô ích cho cây chuyên mục + highlights.
    const state = queryClient.getQueryState(queryKeys.forum.boardThreads(BOARD_ID, 1))
    expect(state?.isInvalidated).toBe(false)
  })

  it('still patches the fresh post into the single-post cache', async () => {
    const fresh = makePost({ id: 40 })
    pinMock.mockResolvedValue(fresh)
    queryClient.setQueryData(queryKeys.forum.post(40), makePost({ id: 40, pinned_at: null }))

    const { result } = renderHook(() => usePinForumPost(), { wrapper })
    await act(async () => {
      result.current.mutate({ postId: 40, pinned: true })
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(queryClient.getQueryData<ForumPost>(queryKeys.forum.post(40))?.pinned_at).toBe(
      '2026-09-03 10:05:00',
    )
  })
})
