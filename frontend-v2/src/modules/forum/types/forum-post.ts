import {
  Angry,
  Building2,
  Frown,
  Globe,
  Heart,
  Laugh,
  Star,
  ThumbsUp,
  Users,
} from 'lucide-react'
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

/** Dải cảm xúc (CR-206) — khớp IntEnum `ForumReactionKind` phía backend. */
export type ForumReactionKind = 1 | 2 | 3 | 4 | 5 | 6

/** Thứ tự vẽ trong khay chọn cảm xúc — cùng thứ tự Facebook. */
export const FORUM_REACTION_KINDS: ForumReactionKind[] = [1, 2, 3, 4, 5, 6]

// why: icon phải là lucide (luật icons.md cấm emoji trong UI). Lucide không có
// mặt "ngạc nhiên" nên WOW dùng ngôi sao với nhãn "Tuyệt vời" — chốt cùng
// backend trong docstring `ForumReactionKind`.
export const FORUM_REACTION_META: Record<
  ForumReactionKind,
  { label: string; icon: LucideIcon; className: string; fill: boolean }
> = {
  1: { label: 'Thích', icon: ThumbsUp, className: 'text-primary', fill: true },
  2: { label: 'Yêu thích', icon: Heart, className: 'text-red-500', fill: true },
  3: { label: 'Haha', icon: Laugh, className: 'text-amber-500', fill: false },
  4: { label: 'Tuyệt vời', icon: Star, className: 'text-amber-500', fill: true },
  5: { label: 'Buồn', icon: Frown, className: 'text-sky-500', fill: false },
  6: { label: 'Phẫn nộ', icon: Angry, className: 'text-orange-600', fill: false },
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
 * Định dạng nội dung bài (CR-261) — khớp IntEnum `ForumBodyFormat` backend.
 * `richHtml` = body là HTML đã qua sanitize server; FE chọn đường vẽ theo cột
 * này, KHÔNG đoán bằng cách ngửi chuỗi. Bài cũ + bình luận luôn `plain`.
 */
export const FORUM_BODY_FORMAT = {
  plain: 0,
  richHtml: 1,
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
  /** Giá trị của `FORUM_BODY_FORMAT` — 1 thì `body` là HTML đã lọc (CR-261). */
  body_format: number
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
  /**
   * Thread trong box (F13a/QĐ-D7) — `board_id > 0` thì `title` bắt buộc và
   * `board_name` để thẻ bài trên feed dẫn "đăng trong box X"; bài Bảng tin
   * thuần cả bốn trường đều rỗng/0.
   */
  board_id: number
  title: string
  /** Giá trị của bộ mã `FORUM_PREFIX` (statuses.ts) — 0 = không prefix. */
  prefix: number
  board_name: string
  /**
   * Hoạt động cuối = max(lúc đăng, bình luận cuối) — CHỈ có trong phong bì
   * thread list của box; feed/chi tiết không trả trường này.
   */
  last_activity_at?: string
  /** Mốc ghim (F9a/CR-199) — khác null = bài đang trên dải Thông báo. */
  pinned_at: string | null
  can_delete: boolean
  /** Người xem là quản trị viên diễn đàn (F5) — FE mở menu ẩn/khôi phục/xóa. */
  can_moderate: boolean
  /** Lý do lần ẩn gần nhất — chỉ khác rỗng khi `status === hidden`. */
  hidden_reason: string
  like_count: number
  liked: boolean
  /** Cảm xúc của CHÍNH người xem (CR-206) — 0 = chưa bấm. */
  my_reaction: number
  /** Số lượt theo từng cảm xúc — key là `ForumReactionKind` (JSON hóa thành chuỗi),
   * chỉ chứa kind có người bấm. */
  reactions: Record<number, number>
  comment_count: number
  images: ForumImage[]
}

/** Một trang feed theo con trỏ `before_id` — không có OFFSET, không có tổng số. */
export interface ForumFeedPage {
  items: ForumPost[]
  next_before_id: number
  has_more: boolean
}

/** Bộ lọc gửi lên `GET /api/forum/posts/search` (CR-263) — mọi trường tùy chọn. */
export interface ForumSearchParams {
  /** Từ khóa — khớp LIKE trên nội dung + tiêu đề thread. */
  q?: string
  /** Chữ gõ tay khớp tên nhân sự / mã NV / email của NGƯỜI TẠO. */
  author_q?: string
  /** Ngữ cảnh ĐÓNG BĂNG trên bài lúc đăng, không phải phòng/công ty hiện tại. */
  company_id?: number
  dept_id?: number
  /** Chỉ quản trị dùng được (1 = đang hiện, 2 = đang ẩn) — người thường bị bỏ qua. */
  status?: number
  page?: number
  /** Ô gợi ý trên header (bao-CR-273.1) chỉ lấy top 5 — bỏ trống là cỡ trang mặc định. */
  per_page?: number
}

/** Một trang kết quả tìm kiếm — phân trang số trang như thread list. */
export interface ForumSearchPage {
  items: ForumPost[]
  total: number
  page: number
  per_page: number
  has_more: boolean
}

/** Tùy chọn hai ô lọc của màn tìm kiếm — distinct từ chính bảng bài viết. */
export interface ForumSearchFilters {
  companies: { id: number; name: string }[]
  departments: { id: number; name: string }[]
}

/** Một người đã bày tỏ cảm xúc — kết quả `GET /api/forum/posts/{id}/likes`. */
export interface ForumPostLiker {
  user_id: number
  name: string
  /** Cảm xúc người này bấm (CR-206) — giá trị của `ForumReactionKind`. */
  kind: number
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
  /** Gửi `FORUM_BODY_FORMAT.richHtml` khi `body` là HTML từ RichTextField (CR-261). */
  body_format?: number
  audience: ForumAudience
  file_ids: number[]
  /** Bỏ trống = bài thường; bài sự kiện (F10) truyền giá trị của `FORUM_POST_KIND`. */
  kind?: number
  /** Đăng thread vào box (F13a) — có `board_id` thì `title` bắt buộc,
   * `audience` bị backend ép theo box nên gửi gì cũng được. */
  board_id?: number
  title?: string
  prefix?: number
}
