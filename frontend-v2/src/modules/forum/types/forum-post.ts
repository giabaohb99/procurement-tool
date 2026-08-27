import { Building2, Globe, Users } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

/** Đối tượng xem của bài viết — khớp IntEnum `ForumAudience` phía backend. */
export type ForumAudience = 1 | 2 | 3

// why: bộ nhãn này khai TAY chứ không sinh từ `gen_status_ts.py` — status_catalog
// chỉ nhận code set dạng CHUỖI (khuôn QĐ-9 của thu mua cũ), còn `ForumAudience`
// là SMALLINT IntEnum theo QĐ-11 nên không đăng ký vào đó được. Chỉ ba giá trị,
// đổi là phải đổi đồng thời backend, nên rủi ro lệch nhãn chấp nhận được.
export const FORUM_AUDIENCE_META: Record<
  ForumAudience,
  { label: string; icon: LucideIcon }
> = {
  1: { label: 'Phòng ban', icon: Users },
  2: { label: 'Công ty', icon: Building2 },
  3: { label: 'Toàn tập đoàn', icon: Globe },
}

/**
 * Loại bài (F10) — khớp IntEnum `ForumPostKind` phía backend: bài SỰ KIỆN vẫn
 * do chính chủ bấm đăng, `kind` chỉ để thẻ bài vẽ dòng hệ thống ("đã cập nhật
 * ảnh đại diện") tách khỏi caption. Sự kiện mới sau này = thêm giá trị.
 */
export const FORUM_POST_KIND = {
  normal: 0,
  avatarUpdate: 1,
} as const

/**
 * Trạng thái bài — khớp IntEnum `ForumPostStatus` (F5). API chỉ trả về bài
 * `published`/`hidden` (bài ẩn chỉ tác giả + quản trị viên còn thấy);
 * `removed` không bao giờ ra tới FE.
 */
export const FORUM_POST_STATUS = {
  pendingReview: 0,
  published: 1,
  hidden: 2,
  removed: 3,
} as const

/** Ảnh/video của bài viết. `url` là địa chỉ nhúng thẳng được (R2 public / uploads). */
export interface ForumImage {
  link_id: number
  file_id: number
  filename: string
  url: string
  /** Bản thumbnail sinh lúc upload — ô lưới feed đọc bản này cho nhẹ băng thông,
   * đèn chiếu mới tải `url` gốc. Rỗng (tệp cũ / video / gif) thì fallback `url`. */
  thumb_url: string
  content_type: string
  size: number
}

/** `PostOut` của hợp đồng API F1 (doc `erp/dien-dan/02` mục F1). */
export interface ForumPost {
  id: number
  body: string
  status: number
  audience: ForumAudience
  kind: number
  dept_id: number | null
  company_id: number | null
  /** Tác giả tính theo TÀI KHOẢN (`user_id`), không phải nhân sự. */
  author_id: number
  author_name: string
  author_code: string
  author_avatar: string
  created_at: string
  can_delete: boolean
  /** Người xem là quản trị viên diễn đàn (F5) — FE mở menu ẩn/khôi phục/xóa. */
  can_moderate: boolean
  /** Lý do lần ẩn gần nhất — chỉ khác rỗng khi `status === hidden`. */
  hidden_reason: string
  like_count: number
  liked: boolean
  comment_count: number
  images: ForumImage[]
}

/** Một trang feed theo con trỏ `before_id` — không có OFFSET, không có tổng số. */
export interface ForumFeedPage {
  items: ForumPost[]
  next_before_id: number
  has_more: boolean
}

/** Một người đã thích bài — kết quả `GET /api/forum/posts/{id}/likes`. */
export interface ForumPostLiker {
  user_id: number
  name: string
}

/** Một ảnh vừa tải lên, chờ gắn vào bài (kết quả `/api/attachments/upload-file`). */
export interface ForumUploadedFile {
  file_id: number
  filename: string
  url: string
  /** Xem ghi chú ở `ForumImage.thumb_url` — dùng cho ô xem trước trong hộp đăng bài. */
  thumb_url: string
  content_type: string
  size: number
}

/** Thân bài đăng lên `POST /api/forum/posts` (hợp đồng API F1). */
export interface NewForumPost {
  body: string
  audience: ForumAudience
  file_ids: number[]
  /** Bỏ trống = bài thường; bài sự kiện (F10) truyền giá trị của `FORUM_POST_KIND`. */
  kind?: number
}
