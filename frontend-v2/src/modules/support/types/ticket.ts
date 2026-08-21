/**
 * Kiểu dữ liệu của phân hệ Phiếu hỗ trợ.
 * Khớp `backend/app/modules/ticket` (controller `_out`).
 */

/** Một tệp đính kèm — dùng cho cả tệp gửi kèm lúc tạo phiếu lẫn tệp trong tin nhắn. */
export interface TicketFile {
  id: number
  file_id: number
  filename: string
  /** Đường đọc thẳng kho lưu trữ (ảnh xem ngay); tệp khác mở tab mới. */
  url: string
  content_type: string
  size: number
}

/** Một lượt trao đổi. `is_staff` = do nhóm Hỗ trợ gửi (bong bóng bên phải). */
export interface TicketMessage {
  id: number
  body: string
  is_staff: boolean
  author_id: number
  author_name: string
  author_avatar?: string
  created_at: string
  files?: TicketFile[]
}

/** Bản rút gọn ở danh sách — KHÔNG kèm `messages`. */
export interface Ticket {
  id: number
  code: string
  subject: string
  department: string
  priority: string
  priority_label: string
  status: string
  status_label: string
  company_id: number
  requester_id: number
  requester_name: string
  requester_avatar?: string
  assignee_id: number
  assignee_name: string
  assignee_avatar?: string
  origin_url?: string
  created_at: string
  updated_at: string
  closed_at?: string
}

/** Chi tiết phiếu — kèm luồng trao đổi. */
export interface TicketDetail extends Ticket {
  messages: TicketMessage[]
}
