import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiGet, apiPost } from '@/core/api'

import { FORUM_POST_KIND, FORUM_POST_STATUS } from '../types/forum-post'
import type { ForumPost } from '../types/forum-post'
import { PostCard } from './post-card'

vi.mock('@/core/api', () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiDelete: vi.fn(),
}))

function makePost(overrides: Partial<ForumPost> = {}): ForumPost {
  return {
    id: 1,
    body: 'nội dung thử',
    status: 1,
    audience: 3,
    kind: FORUM_POST_KIND.normal,
    dept_id: null,
    company_id: null,
    author_id: 9,
    author_name: 'Trần Thử Nghiệm',
    author_code: 'NV001',
    author_avatar: '',
    created_at: '2026-08-27T08:00:00',
    can_delete: false,
    can_moderate: false,
    hidden_reason: '',
    like_count: 0,
    liked: false,
    comment_count: 0,
    images: [],
    ...overrides,
  }
}

function renderCard(post: ForumPost) {
  // PostCard nay tự mang hook like (useMutation) nên phải bọc QueryClientProvider.
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <PostCard post={post} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('PostCard — dòng hệ thống của bài sự kiện (F10)', () => {
  it('bài đổi ảnh đại diện hiện "đã cập nhật ảnh đại diện" cạnh tên tác giả', () => {
    renderCard(makePost({ kind: FORUM_POST_KIND.avatarUpdate }))
    expect(screen.getByText('đã cập nhật ảnh đại diện')).toBeInTheDocument()
  })

  it('bài thường không hiện dòng hệ thống', () => {
    renderCard(makePost())
    expect(screen.queryByText('đã cập nhật ảnh đại diện')).not.toBeInTheDocument()
  })
})

describe('PostCard — kiểm duyệt (F5)', () => {
  it('bài bị ẩn hiện nhãn kèm lý do cho tác giả/quản trị viên', () => {
    renderCard(
      makePost({ status: FORUM_POST_STATUS.hidden, hidden_reason: 'đăng nhầm nhóm' }),
    )
    expect(screen.getByText(/đã bị quản trị viên ẩn/)).toBeInTheDocument()
    expect(screen.getByText('đăng nhầm nhóm')).toBeInTheDocument()
  })

  it('bài thường không hiện nhãn ẩn', () => {
    renderCard(makePost())
    expect(screen.queryByText(/đã bị quản trị viên ẩn/)).not.toBeInTheDocument()
  })

  it('quản trị viên thấy menu «...» dù không phải tác giả, kèm mục Ẩn và Gỡ', async () => {
    renderCard(makePost({ can_moderate: true }))
    await userEvent.click(screen.getByRole('button', { name: 'Thao tác với bài viết' }))
    expect(await screen.findByText('Ẩn bài viết')).toBeInTheDocument()
    expect(screen.getByText('Gỡ bài viết')).toBeInTheDocument()
    // Không phải tác giả thì không có mục xóa của tác giả.
    expect(screen.queryByText('Xóa bài')).not.toBeInTheDocument()
  })

  it('bài đang ẩn thì mục Ẩn đổi thành Khôi phục', async () => {
    renderCard(makePost({ can_moderate: true, status: FORUM_POST_STATUS.hidden }))
    await userEvent.click(screen.getByRole('button', { name: 'Thao tác với bài viết' }))
    expect(await screen.findByText('Khôi phục bài viết')).toBeInTheDocument()
    expect(screen.queryByText('Ẩn bài viết')).not.toBeInTheDocument()
  })

  it('người thường không phải tác giả thì không thấy menu «...»', () => {
    renderCard(makePost())
    expect(
      screen.queryByRole('button', { name: 'Thao tác với bài viết' }),
    ).not.toBeInTheDocument()
  })
})

describe('PostCard — popup chi tiết (kiểu Facebook)', () => {
  // Trước đây bấm Bình luận là điều hướng sang /forum/posts/:id, quay lại mất
  // vị trí cuộn — nay phải mở dialog ngay tại chỗ.
  it('bấm Bình luận mở popup chi tiết kèm khối bình luận, không rời bảng tin', async () => {
    vi.mocked(apiGet).mockResolvedValue({ items: [], older_count: 0, oldest_id: 0 })
    renderCard(makePost())

    await userEvent.click(screen.getByRole('button', { name: 'Bình luận' }))

    expect(await screen.findByText('Bài viết của Trần Thử Nghiệm')).toBeInTheDocument()
    expect(await screen.findByText(/Chưa có bình luận nào/)).toBeInTheDocument()
  })

  it('số bình luận là nút mở popup, không còn link sang trang riêng', async () => {
    vi.mocked(apiGet).mockResolvedValue({ items: [], older_count: 0, oldest_id: 0 })
    renderCard(makePost({ comment_count: 2 }))

    const links = screen.queryAllByRole('link')
    expect(links.map((a) => a.getAttribute('href'))).not.toContain('/forum/posts/1')

    await userEvent.click(screen.getByRole('button', { name: '2 bình luận' }))
    expect(await screen.findByText('Bài viết của Trần Thử Nghiệm')).toBeInTheDocument()
  })
})

describe('PostCard — thích bài (F4)', () => {
  it('bấm Thích gọi đúng API like của bài', async () => {
    vi.mocked(apiPost).mockResolvedValue({ liked: true, count: 1 })
    renderCard(makePost())

    await userEvent.click(screen.getByRole('button', { name: 'Thích' }))

    await waitFor(() =>
      expect(apiPost).toHaveBeenCalledWith('/api/forum/posts/1/like', {}),
    )
  })

  it('bấm số lượt thích mở hộp "Người đã thích" và nạp danh sách', async () => {
    vi.mocked(apiGet).mockResolvedValue([{ user_id: 2, name: 'Người Thích Một' }])
    renderCard(makePost({ like_count: 3 }))

    await userEvent.click(screen.getByRole('button', { name: '3' }))

    expect(await screen.findByText('Người đã thích')).toBeInTheDocument()
    expect(await screen.findByText('Người Thích Một')).toBeInTheDocument()
    expect(apiGet).toHaveBeenCalledWith('/api/forum/posts/1/likes')
  })
})
