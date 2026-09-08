import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type { ForumPost } from '../types/forum-post'
import { ForumHeaderSearch } from './forum-header-search'

const quickSearchMock = vi.hoisted(() => vi.fn())

vi.mock('../hooks/use-forum-quick-search', async (importOriginal) => ({
  //  Giữ nguyên hằng MIN/LIMIT thật — chỉ thế phần gọi API; hằng thật đổi mà
  //  component quên theo thì test phải đỏ.
  ...(await importOriginal<Record<string, unknown>>()),
  useForumQuickSearch: quickSearchMock,
}))

function post(over: Partial<ForumPost>): ForumPost {
  return {
    id: 1, body: 'nội dung', body_format: 0, status: 1, audience: 3, kind: 1,
    board_id: 0, title: '', prefix: 0, board_name: '',
    dept_id: 0, company_id: 0,
    author_id: 9, author_name: 'Chín Nút', author_code: '', author_avatar: '',
    created_at: '2026-09-01T08:00:00', pinned_at: '',
    can_delete: false, can_moderate: false,
    like_count: 0, liked: false, my_reaction: 0, reactions: {},
    comment_count: 0, images: [], hidden_reason: '',
    ...over,
  } as ForumPost
}

/** Hiện đường dẫn hiện tại để khẳng định điều hướng mà không dựng cả router thật. */
function LocationSpy() {
  const location = useLocation()
  return <p data-testid="location">{location.pathname + location.search}</p>
}

function mount() {
  return render(
    <MemoryRouter>
      <ForumHeaderSearch />
      <LocationSpy />
    </MemoryRouter>,
  )
}

describe('ForumHeaderSearch', () => {
  it('keeps the dropdown closed under the minimum keyword length', async () => {
    quickSearchMock.mockReturnValue({ isPending: true, data: undefined })
    mount()
    await userEvent.type(screen.getByRole('textbox', { name: 'Tìm bài viết' }), 'a')
    expect(screen.queryByText('Đang tìm...')).not.toBeInTheDocument()
  })

  it('shows top results with a view-all count once typed enough', async () => {
    quickSearchMock.mockReturnValue({
      isPending: false,
      data: {
        items: [
          post({ id: 7, title: 'Nội quy phòng ăn', board_name: 'Thông báo chung' }),
          post({ id: 8, title: '', body: '<p>bài <strong>rich</strong></p>', body_format: 1 }),
        ],
        total: 12, page: 1, per_page: 5, has_more: true,
      },
    })
    mount()
    await userEvent.type(screen.getByRole('textbox', { name: 'Tìm bài viết' }), 'nội quy')
    expect(screen.getByText('Nội quy phòng ăn')).toBeInTheDocument()
    // meta = người đăng + box; bài rich phải bóc thẻ HTML thành chữ trơn
    expect(screen.getByText('Chín Nút · Thông báo chung')).toBeInTheDocument()
    expect(screen.getByText('bài rich')).toBeInTheDocument()
    expect(screen.getByText('Xem tất cả 12 kết quả')).toBeInTheDocument()
  })

  it('navigates straight to the post when a suggestion is clicked', async () => {
    quickSearchMock.mockReturnValue({
      isPending: false,
      data: { items: [post({ id: 7, title: 'Nội quy phòng ăn' })], total: 1, page: 1, per_page: 5, has_more: false },
    })
    mount()
    await userEvent.type(screen.getByRole('textbox', { name: 'Tìm bài viết' }), 'nội quy')
    await userEvent.click(screen.getByText('Nội quy phòng ăn'))
    expect(screen.getByTestId('location')).toHaveTextContent('/forum/posts/7')
  })

  it('goes to the full search page with ?q= on Enter and on view-all', async () => {
    quickSearchMock.mockReturnValue({
      isPending: false,
      data: { items: [post({ id: 7, title: 'Nội quy phòng ăn' })], total: 12, page: 1, per_page: 5, has_more: true },
    })
    mount()
    const input = screen.getByRole('textbox', { name: 'Tìm bài viết' })
    await userEvent.type(input, 'nội quy{Enter}')
    expect(screen.getByTestId('location')).toHaveTextContent('/forum/search?q=n%E1%BB%99i%20quy')
  })

  it('picks the highlighted suggestion with arrow keys + Enter', async () => {
    quickSearchMock.mockReturnValue({
      isPending: false,
      data: {
        items: [post({ id: 7, title: 'Bài một' }), post({ id: 8, title: 'Bài hai' })],
        total: 2, page: 1, per_page: 5, has_more: false,
      },
    })
    mount()
    const input = screen.getByRole('textbox', { name: 'Tìm bài viết' })
    await userEvent.type(input, 'bài{ArrowDown}{ArrowDown}{Enter}')
    expect(screen.getByTestId('location')).toHaveTextContent('/forum/posts/8')
  })

  it('shows the empty message but still offers the advanced-filter door', async () => {
    quickSearchMock.mockReturnValue({
      isPending: false,
      data: { items: [], total: 0, page: 1, per_page: 5, has_more: false },
    })
    mount()
    await userEvent.type(screen.getByRole('textbox', { name: 'Tìm bài viết' }), 'zzz')
    expect(screen.getByText('Không có bài viết nào khớp.')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Bộ lọc nâng cao' }))
    expect(screen.getByTestId('location')).toHaveTextContent('/forum/search?q=zzz')
  })
})
