import type { ForumPost } from './forum-post'

/**
 * Chuyên mục kiểu VOZ (F13a/F13b, QĐ-D7). Backend trả CÂY hai tầng: nhóm
 * (`parent_id = 0`, chỉ làm tiêu đề) chứa các box (`parent_id > 0`, nơi đăng
 * thread). Người thường chỉ nhận box đang mở; `forum_admin` nhận cả box ẩn
 * kèm `status` để còn dọn.
 */

/** Khớp IntEnum `ForumBoardStatus` phía backend. */
export const FORUM_BOARD_STATUS = {
  active: 1,
  hidden: 2,
} as const

/** Khối bài-mới-nhất của một box — dòng bấm được trên màn `/forum/boards`. */
export interface ForumBoardLastPost {
  post_id: number
  title: string
  prefix: number
  /** Hoạt động cuối = max(lúc đăng, bình luận cuối) — cùng công thức sắp thread. */
  last_at: string
  last_user_id: number
  last_author_name: string
  last_author_avatar: string
}

/** Một nút trên cây — nhóm hay box cùng hình dạng, phân biệt bằng `parent_id`. */
export interface ForumBoardNode {
  id: number
  /** 0 = nhóm tiêu đề; > 0 = box thuộc nhóm đó. */
  parent_id: number
  name: string
  description: string
  /** Tên icon lucide (kebab-case) hoặc 1 emoji do admin gõ lúc tạo box. */
  icon: string
  sort_order: number
  status: number
  audience: number
  thread_count: number
  comment_count: number
  last_post: ForumBoardLastPost | null
}

/** Nhóm tiêu đề kèm các box con — phần tử của `GET /api/forum/boards`. */
export interface ForumBoardGroup extends ForumBoardNode {
  children: ForumBoardNode[]
}

/** Đầu phiếu box trả kèm trong phong bì thread — vẽ header màn `/forum/boards/:id`. */
export interface ForumBoardHeader {
  id: number
  name: string
  icon: string
  description: string
  status: number
}

/** Một dòng thread GỌN cho sidebar (F13c) — chỉ đủ để dẫn đường, không body/ảnh. */
export interface ForumThreadSummary {
  id: number
  title: string
  prefix: number
  board_id: number
  board_name: string
  comment_count: number
  created_at: string
}

/** Hai khối máy tự xếp của sidebar «Diễn đàn» — khối «Nổi bật» đi API bài ghim riêng. */
export interface ForumBoardHighlights {
  /** Top thread theo bình luận + reaction 7 ngày gần nhất. */
  trending: ForumThreadSummary[]
  /** Thread mới toàn diễn đàn, id giảm dần. */
  latest: ForumThreadSummary[]
}

/** Một trang thread của box — phân trang SỐ TRANG (khác feed con trỏ). */
export interface ForumBoardThreadsPage {
  items: ForumPost[]
  total: number
  page: number
  per_page: number
  has_more: boolean
  board: ForumBoardHeader
}
