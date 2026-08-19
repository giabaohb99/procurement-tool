import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
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
 * Danh sách thông báo có PHÂN TRANG — dùng cho trang `/notifications`.
 *
 * Tách khỏi `useNotifications` ở trên vì cái chuông cố định trang 1 / 20 dòng,
 * còn trang đầy đủ thì đổi trang, đổi cỡ trang và có ô tìm kiếm. Vẫn dùng chung
 * tiền tố khóa `notification` nên mọi thao tác (đọc, xóa) vô hiệu một lần là cả
 * chuông lẫn trang cùng nạp lại.
 *
 * KHÔNG tự hỏi lại theo nhịp: người dùng đang đọc mà danh sách nhảy một cái là
 * mất chỗ. Chuông vẫn poll 20 giây nên số chưa đọc vẫn tươi.
 */
export function useNotificationList(params: ListParams) {
  return useQuery({
    queryKey: queryKeys.notification.list(params),
    queryFn: () => notificationApi.list(params),
    // Giữ dữ liệu trang cũ trong lúc tải trang mới: bảng không chớp trắng.
    placeholderData: (previous) => previous,
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

/**
 * Các thao tác trên thông báo; xong việc thì nạp lại cả nhóm `notification` —
 * một lần vô hiệu là chuông và trang danh sách cùng khớp lại số chưa đọc.
 */
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

  const remove = useMutation({
    mutationFn: (id: number) => notificationApi.remove(id),
    onSuccess: refresh,
  })

  return { markRead, readAll, clearRead, remove }
}
