import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { notificationApi } from './notification-api'

/** Nhịp hỏi lại server. 20 giây như app cũ: đủ nhanh để thấy việc mới. */
const POLL_MS = 20_000

/** Chuông chỉ xem nhanh; nhiều hơn nữa thì cuộn trong danh sách. */
export const BELL_LIMIT = 20

/**
 * Thông báo của chính người dùng, tự hỏi lại mỗi 20 giây.
 *
 * `unreadOnly` đổi bộ lọc của DANH SÁCH, không đổi số trên chuông: backend luôn
 * trả `unread` là tổng chưa đọc bất kể đang lọc gì.
 */
export function useNotifications(unreadOnly: boolean) {
  const params = {
    page: 1,
    page_size: BELL_LIMIT,
    ...(unreadOnly ? { unread: 'true' } : {}),
  }

  return useQuery({
    queryKey: queryKeys.notification.list(params),
    queryFn: () => notificationApi.list(params),
    refetchInterval: POLL_MS,
    // Hỏng mạng một nhịp thì nhịp sau tự hỏi lại, khỏi phải thử lại ngay.
    retry: false,
  })
}

/**
 * Cảnh báo hệ thống (giao hàng trễ, công nợ quá hạn…).
 *
 * Backend tính lại từ đầu mỗi lần gọi nên đắt hơn danh sách thông báo — vẫn để
 * chung nhịp 20 giây cho số trên chuông khớp với danh sách bên trong.
 */
export function useSystemAlerts() {
  return useQuery({
    queryKey: queryKeys.notification.alerts(),
    queryFn: () => notificationApi.alerts(),
    refetchInterval: POLL_MS,
    retry: false,
  })
}

/** Ba thao tác của chuông; xong việc thì nạp lại cả nhóm `notification`. */
export function useNotificationActions() {
  const queryClient = useQueryClient()
  const refresh = () =>
    void queryClient.invalidateQueries({ queryKey: queryKeys.notification.all })

  const markRead = useMutation({
    mutationFn: (id: number) => notificationApi.markRead(id),
    onSuccess: refresh,
  })

  const readAll = useMutation({
    mutationFn: () => notificationApi.readAll(),
    onSuccess: refresh,
  })

  const clearRead = useMutation({
    mutationFn: () => notificationApi.clearRead(),
    onSuccess: refresh,
  })

  return { markRead, readAll, clearRead }
}
