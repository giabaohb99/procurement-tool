import type { ListParams } from '@/shared/types/api'

/** Hai chế độ xem của danh sách thông báo. */
export type NotificationTab = 'all' | 'unread'

export interface NotificationFilter {
  page: number
  pageSize: number
  tab: NotificationTab
  search: string
}

/**
 * Dịch bộ lọc trên màn hình thành tham số gửi cho `/api/notifications`.
 *
 * Tách khỏi component để kiểm được bằng test: chỗ này sai thì màn hình vẫn vẽ
 * ra bình thường, chỉ có điều lọc "Chưa đọc" lại trả về tất cả — kiểu lỗi âm
 * thầm khó thấy nhất.
 *
 * Hai quy ước phải giữ:
 *  - `unread` chỉ gửi khi ĐANG lọc chưa đọc; gửi `unread: 'false'` thì backend
 *    vẫn coi là có tham số và hiểu khác ý.
 *  - từ khóa rỗng (kể cả toàn khoảng trắng) thì BỎ HẲN `q`, không gửi chuỗi
 *    rỗng — nếu không, mỗi lần xóa hết ô tìm là một khóa cache khác nhau.
 */
export function buildNotificationParams({
  page,
  pageSize,
  tab,
  search,
}: NotificationFilter): ListParams {
  const keyword = search.trim()
  return {
    page,
    page_size: pageSize,
    ...(tab === 'unread' ? { unread: 'true' } : {}),
    ...(keyword ? { q: keyword } : {}),
  }
}
