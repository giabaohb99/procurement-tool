import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type { ForumThreadSummary } from '../types/forum-board'
import type { ForumPost } from '../types/forum-post'
import { BoardsSidebar, PinnedSpotlight } from './boards-sidebar'

const pinnedMock = vi.hoisted(() => vi.fn())
const highlightsMock = vi.hoisted(() => vi.fn())

vi.mock('../hooks/use-pinned-posts', () => ({ usePinnedPosts: pinnedMock }))
vi.mock('../hooks/use-board-highlights', () => ({ useBoardHighlights: highlightsMock }))

function post(over: Partial<ForumPost>): ForumPost {
  return {
    id: 1, body: 'nội dung', body_format: 0, status: 1, audience: 3, kind: 1,
    board_id: 0, title: '', prefix: 0, board_name: '',
    dept_id: 0, company_id: 0,
    author_id: 9, author_name: 'A', author_code: '', author_avatar: '',
    created_at: '2026-09-01T08:00:00', pinned_at: '2026-09-02T08:00:00',
    can_delete: false, can_moderate: false,
    like_count: 0, liked: false, my_reaction: 0, reactions: {},
    comment_count: 0, images: [], hidden_reason: '',
    ...over,
  } as ForumPost
}

function thread(over: Partial<ForumThreadSummary>): ForumThreadSummary {
  return {
    id: 10, title: 'Chủ đề', prefix: 0, board_id: 5, board_name: 'Góc chia sẻ',
    comment_count: 0, created_at: '2026-09-01T08:00:00',
    ...over,
  }
}

function mount(ui: React.ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>)
}

describe('BoardsSidebar', () => {
  it('renders the three blocks with their data', () => {
    pinnedMock.mockReturnValue({ isPending: false, data: [post({ id: 1, title: 'Thông báo ghim' })] })
    highlightsMock.mockReturnValue({
      isPending: false,
      data: {
        trending: [thread({ id: 10, title: 'Bài sôi nổi', comment_count: 7 })],
        latest: [thread({ id: 11, title: 'Bài mới toanh' })],
      },
    })
    mount(<BoardsSidebar />)
    expect(screen.getByText('Nổi bật')).toBeInTheDocument()
    expect(screen.getByText('Thông báo ghim')).toBeInTheDocument()
    expect(screen.getByText('Đang sôi nổi')).toBeInTheDocument()
    expect(screen.getByText('Bài sôi nổi')).toBeInTheDocument()
    // meta của khối sôi nổi = box + SỐ BÌNH LUẬN (không phải mốc thời gian)
    expect(screen.getByText('Góc chia sẻ · 7 bình luận')).toBeInTheDocument()
    expect(screen.getByText('Mới nhất')).toBeInTheDocument()
    expect(screen.getByText('Bài mới toanh')).toBeInTheDocument()
  })

  it('renders nothing at all when every block is empty', () => {
    // sidebar là khối phụ trợ — rỗng thì biến hẳn, không chừa khung trắng
    pinnedMock.mockReturnValue({ isPending: false, data: [] })
    highlightsMock.mockReturnValue({ isPending: false, data: { trending: [], latest: [] } })
    const { container } = mount(<BoardsSidebar />)
    expect(container).toBeEmptyDOMElement()
  })
})

describe('PinnedSpotlight', () => {
  it('falls back to the body when a pinned feed post has no title', () => {
    pinnedMock.mockReturnValue({
      isPending: false,
      data: [post({ id: 2, title: '', body: 'Bài ghim không tiêu đề' })],
    })
    highlightsMock.mockReturnValue({ isPending: false, data: undefined })
    mount(<PinnedSpotlight />)
    expect(screen.getByText('Bài ghim không tiêu đề')).toBeInTheDocument()
  })

  it('strips markup from a rich pinned post so the label shows plain text (CR-261)', () => {
    pinnedMock.mockReturnValue({
      isPending: false,
      data: [post({ id: 3, title: '', body: '<p>ghim <strong>đậm</strong></p>', body_format: 1 })],
    })
    highlightsMock.mockReturnValue({ isPending: false, data: undefined })
    mount(<PinnedSpotlight />)
    expect(screen.getByText('ghim đậm')).toBeInTheDocument()
  })

  it('renders nothing when there is no pinned post', () => {
    pinnedMock.mockReturnValue({ isPending: false, data: [] })
    const { container } = mount(<PinnedSpotlight />)
    expect(container).toBeEmptyDOMElement()
  })
})
