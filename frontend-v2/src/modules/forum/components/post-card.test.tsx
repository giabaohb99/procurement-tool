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
    pinned_at: null,
    can_delete: false,
    can_moderate: false,
    hidden_reason: '',
    like_count: 0,
    liked: false,
    my_reaction: 0,
    reactions: {},
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

describe('PostCard — ghim bài (F9a/CR-199)', () => {
  it('bài đang ghim hiện nhãn «Đã ghim» trên đầu bài', () => {
    renderCard(makePost({ pinned_at: '2026-08-27T09:00:00' }))
    expect(screen.getByText('Đã ghim')).toBeInTheDocument()
  })

  it('bài thường không hiện nhãn ghim', () => {
    renderCard(makePost())
    expect(screen.queryByText('Đã ghim')).not.toBeInTheDocument()
  })

  it('quản trị viên thấy «Ghim bài viết» với bài đang hiển thị', async () => {
    renderCard(makePost({ can_moderate: true }))
    await userEvent.click(screen.getByRole('button', { name: 'Thao tác với bài viết' }))
    expect(await screen.findByText('Ghim bài viết')).toBeInTheDocument()
  })

  it('bài đã ghim thì mục Ghim đổi thành «Bỏ ghim bài viết»', async () => {
    renderCard(makePost({ can_moderate: true, pinned_at: '2026-08-27T09:00:00' }))
    await userEvent.click(screen.getByRole('button', { name: 'Thao tác với bài viết' }))
    expect(await screen.findByText('Bỏ ghim bài viết')).toBeInTheDocument()
    expect(screen.queryByText('Ghim bài viết')).not.toBeInTheDocument()
  })

  it('bài đang ẨN không có mục Ghim — ghim bài ẩn là treo thông báo không ai đọc được', async () => {
    renderCard(makePost({ can_moderate: true, status: FORUM_POST_STATUS.hidden }))
    await userEvent.click(screen.getByRole('button', { name: 'Thao tác với bài viết' }))
    expect(await screen.findByText('Khôi phục bài viết')).toBeInTheDocument()
    expect(screen.queryByText('Ghim bài viết')).not.toBeInTheDocument()
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

describe('PostCard — cảm xúc kiểu Facebook (CR-206)', () => {
  it('bấm nhanh nút Thích gọi API với kind=1', async () => {
    vi.mocked(apiPost).mockResolvedValue({
      liked: true,
      count: 1,
      my_reaction: 1,
      reactions: { 1: 1 },
    })
    renderCard(makePost())

    await userEvent.click(screen.getByRole('button', { name: 'Thích' }))

    await waitFor(() =>
      expect(apiPost).toHaveBeenCalledWith('/api/forum/posts/1/like', { kind: 1 }),
    )
  })

  it('đang có cảm xúc thì nút mang nhãn cảm xúc đó, bấm là bỏ đúng kind đang có', async () => {
    vi.mocked(apiPost).mockResolvedValue({
      liked: false,
      count: 0,
      my_reaction: 0,
      reactions: {},
    })
    renderCard(makePost({ my_reaction: 2, liked: true, like_count: 1, reactions: { 2: 1 } }))

    // Nhãn nút đổi theo cảm xúc của mình — không còn chữ "Thích" chết cứng.
    await userEvent.click(screen.getByRole('button', { name: 'Yêu thích' }))

    await waitFor(() =>
      expect(apiPost).toHaveBeenCalledWith('/api/forum/posts/1/like', { kind: 2 }),
    )
  })

  it('rê chuột lên nút mở khay 6 cảm xúc, chọn Haha gửi kind=3', async () => {
    vi.mocked(apiPost).mockResolvedValue({
      liked: true,
      count: 1,
      my_reaction: 3,
      reactions: { 3: 1 },
    })
    renderCard(makePost())

    await userEvent.hover(screen.getByRole('button', { name: 'Thích' }))
    // Khay mở sau 350ms rê chuột — chờ thật thay vì fake timer cho khỏi lệch userEvent.
    const picker = await screen.findByRole('menu', { name: 'Chọn cảm xúc' })
    expect(picker).toBeInTheDocument()

    await userEvent.click(screen.getByRole('menuitem', { name: 'Haha' }))
    await waitFor(() =>
      expect(apiPost).toHaveBeenCalledWith('/api/forum/posts/1/like', { kind: 3 }),
    )
  })

  it('bấm số lượt mở hộp cảm xúc, có chip lọc theo từng loại khi đủ 2 loại', async () => {
    vi.mocked(apiGet).mockResolvedValue([
      { user_id: 2, name: 'Người Thích Một', kind: 1 },
      { user_id: 3, name: 'Người Yêu Thích', kind: 2 },
    ])
    renderCard(makePost({ like_count: 2, reactions: { 1: 1, 2: 1 } }))

    await userEvent.click(screen.getByRole('button', { name: '2' }))

    expect(await screen.findByText('Cảm xúc về bài viết')).toBeInTheDocument()
    expect(await screen.findByText('Người Thích Một')).toBeInTheDocument()
    expect(apiGet).toHaveBeenCalledWith('/api/forum/posts/1/likes')

    // Lọc theo chip "Yêu thích" thì người bấm Thích biến khỏi danh sách.
    await userEvent.click(screen.getByRole('button', { name: 'Yêu thích' }))
    expect(screen.getByText('Người Yêu Thích')).toBeInTheDocument()
    expect(screen.queryByText('Người Thích Một')).not.toBeInTheDocument()
  })
})
