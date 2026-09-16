import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import {
  systemLogApi,
  type SystemLogFilters,
  type SystemLogListParams,
} from '../api/system-log-api'

/**
 * Nhịp thăm dò của «Theo dõi trực tiếp» — 5 giây, đúng con số ở §8.2 của
 * `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md`.
 *
 * Cách dùng màn này hay gặp nhất là mở hai tab: một tab bấm nút, một tab xem log
 * chạy. Nhanh hơn 5 giây thì bảng nhảy liên tục không đọc kịp; chậm hơn thì mất
 * cảm giác "vừa bấm xong đã thấy".
 */
export const LOG_FOLLOW_INTERVAL_MS = 5000

/**
 * Trang danh sách nhật ký hệ thống.
 *
 * `follow` bật thì thăm dò lại mỗi 5 giây, **kể cả khi cửa sổ không được focus**
 * (`refetchIntervalInBackground`): người ta bật theo dõi rồi chuyển sang tab
 * khác để thao tác — đó chính là lúc cần nó chạy. Không có cờ đó thì quay lại
 * chỉ thấy một lượt nạp duy nhất và nghĩ là hệ thống không ghi gì.
 */
export function useSystemLogs(params: SystemLogListParams, options: { follow?: boolean } = {}) {
  return useQuery({
    queryKey: queryKeys.system.systemLogs(params as Record<string, unknown>),
    queryFn: () => systemLogApi.list(params),
    placeholderData: keepPreviousData,
    staleTime: 5 * 1000,
    refetchInterval: options.follow ? LOG_FOLLOW_INTERVAL_MS : false,
    refetchIntervalInBackground: Boolean(options.follow),
  })
}

/**
 * Số liệu ba biểu đồ — nhận CHÍNH bộ lọc của bảng.
 *
 * `enabled` để tắt khi người dùng thu gọn khu biểu đồ: đây là ba lượt `GROUP BY`
 * trên cùng tập dòng của bảng, không đáng chạy nền cho một khu đang đóng.
 */
export function useSystemLogSummary(
  filters: SystemLogFilters,
  options: { enabled?: boolean; follow?: boolean } = {},
) {
  return useQuery({
    queryKey: queryKeys.system.systemLogSummary(filters as Record<string, unknown>),
    queryFn: () => systemLogApi.summary(filters),
    placeholderData: keepPreviousData,
    staleTime: 30 * 1000,
    enabled: options.enabled ?? true,
    refetchInterval: options.follow ? LOG_FOLLOW_INTERVAL_MS : false,
  })
}

/**
 * Gói bốn tab của MỘT lượt gọi.
 *
 * `staleTime: Infinity` — một lượt gọi đã xong thì ba bảng nhật ký của nó không
 * bao giờ đổi nữa. Nạp lại là tốn công cho một kết quả chắc chắn giống hệt.
 */
export function useSystemLogDetail(requestId: string | null) {
  return useQuery({
    queryKey: queryKeys.system.systemLogDetail(requestId ?? ''),
    queryFn: () => systemLogApi.detail(requestId ?? ''),
    enabled: Boolean(requestId),
    staleTime: Infinity,
  })
}
