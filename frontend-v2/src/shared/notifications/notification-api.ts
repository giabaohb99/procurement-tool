import { apiDelete, apiGet, apiPost } from '@/core/api'
import type { ListParams } from '@/shared/types/api'
import type { NotificationList, SystemAlertList } from './notification-types'

/** Tầng API của chuông thông báo — chỉ gọi HTTP, không chứa logic React. */
export const notificationApi = {
  /** `unread: 'true'` để chỉ lấy chưa đọc; `q` tìm trong tiêu đề / nội dung. */
  list: (params: ListParams) => apiGet<NotificationList>('/api/notifications', { params }),

  alerts: () => apiGet<SystemAlertList>('/api/alerts'),

  markRead: (id: number) => apiPost<null>(`/api/notifications/${id}/read`),

  readAll: () => apiPost<null>('/api/notifications/read-all'),

  /** Xóa MỘT thông báo, đã đọc hay chưa cũng xóa. Chỉ trang danh sách dùng tới. */
  remove: (id: number) => apiDelete<null>(`/api/notifications/${id}`),

  /** Dọn những cái ĐÃ ĐỌC; cái chưa đọc giữ nguyên. */
  clearRead: () => apiDelete<{ deleted: number }>('/api/notifications/read'),
}
