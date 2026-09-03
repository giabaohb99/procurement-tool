/**
 * Kiểu dữ liệu của tab «Quản trị» diễn đàn (CR-263) — chuyên mục, nhật ký
 * kiểm duyệt. Chỉ tài khoản có grant `forum_post`/`forum_board` gọi được các
 * API tương ứng; người thường ăn 403.
 */

/** Thân gửi lên `POST /api/forum/boards` + `PUT /api/forum/boards/{id}`. */
export interface ForumBoardInput {
  name: string
  description: string
  /** Tên icon lucide (kebab-case) hoặc 1 emoji — `BoardIcon` tự vẽ. */
  icon: string
  /** 0 = NHÓM tiêu đề; > 0 = BOX thuộc nhóm đó (đúng hai tầng). */
  parent_id: number
  sort_order: number
  /** Giá trị của `FORUM_BOARD_STATUS` — ẩn là rút khỏi mắt, không xóa. */
  status: number
}

/** Khớp IntEnum `ForumModerationAction` backend (QĐ-D1). */
export const FORUM_MODERATION_ACTION = {
  hide: 1,
  remove: 2,
  restore: 3,
} as const

/** Một dòng `GET /api/forum/moderation-logs` — bảng ghi từ F5, đọc từ CR-263. */
export interface ForumModerationLogEntry {
  id: number
  post_id: number
  /** Tiêu đề thread hoặc trích nội dung — backend đã bóc thẻ bài rich. */
  post_label: string
  /** `FORUM_POST_STATUS` hiện tại của bài — REMOVED thì không mở link được nữa. */
  post_status: number
  /** Giá trị của `FORUM_MODERATION_ACTION`. */
  action: number
  reason: string
  actor_id: number
  actor_name: string
  created_at: string
  /** Mốc đã bắn chuông cho tác giả — null khi admin tự xử bài mình. */
  notified_at: string | null
}

/** Một trang nhật ký kiểm duyệt, mới → cũ. */
export interface ForumModerationLogPage {
  items: ForumModerationLogEntry[]
  total: number
  page: number
  per_page: number
  has_more: boolean
}
