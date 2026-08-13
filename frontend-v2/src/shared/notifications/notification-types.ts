/** Một thông báo gửi riêng cho người dùng — khớp `_out()` của backend. */
export interface AppNotification {
  id: number
  title: string
  body: string
  /** Đường dẫn của app CŨ; đổi sang đường dẫn v2 bằng `toAppPath()`. */
  link: string
  is_read: boolean
  /** ISO string, giờ UTC. */
  at: string
}

export interface NotificationList {
  /** Tổng chưa đọc — KHÔNG phụ thuộc bộ lọc đang xem, dùng để hiện số trên chuông. */
  unread: number
  total: number
  page: number
  page_size: number
  items: AppNotification[]
}

/**
 * CẢNH BÁO hệ thống (`/api/alerts`) — khác thông báo ở chỗ không ai "gửi" cả:
 * backend tính lại mỗi lần gọi từ dữ liệu đang có (giao hàng trễ, công nợ quá
 * hạn, hợp đồng sắp hết hạn) và chỉ trả phần người xem có quyền đọc.
 */
export interface SystemAlert {
  type: string
  level: 'danger' | 'warn'
  title: string
  link: string
}

export interface SystemAlertList {
  total: number
  danger: number
  warn: number
  items: SystemAlert[]
}
