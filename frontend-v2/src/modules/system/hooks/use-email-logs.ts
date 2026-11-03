import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import {
  fetchEmailLogDetail,
  fetchEmailLogMeta,
  fetchEmailLogStats,
  fetchEmailLogs,
  type EmailLogFilters,
} from '../api/email-log-api'

/** Danh sách thư đã ghi, mới nhất trước (bao-CR-721). */
export function useEmailLogs(params: EmailLogFilters) {
  return useQuery({
    queryKey: queryKeys.system.emailLogs(params as Record<string, unknown>),
    queryFn: () => fetchEmailLogs(params),
    placeholderData: keepPreviousData,
    staleTime: 10 * 1000,
  })
}

/** Bộ chọn ô lọc — danh mục mẫu email chỉ đổi sau một lần deploy, trong phiên là hằng. */
export function useEmailLogMeta() {
  return useQuery({
    queryKey: queryKeys.system.emailLogMeta(),
    queryFn: fetchEmailLogMeta,
    staleTime: Infinity,
  })
}

/** Thẻ "N thư lỗi 7 ngày qua" đầu màn. */
export function useEmailLogStats(days = 7) {
  return useQuery({
    queryKey: queryKeys.system.emailLogStats(days),
    queryFn: () => fetchEmailLogStats(days),
    staleTime: 30 * 1000,
  })
}

/** Một dòng đầy đủ — dòng đã ghi không đổi nữa nên giữ vô hạn trong phiên. */
export function useEmailLogDetail(id: number | null) {
  return useQuery({
    queryKey: queryKeys.system.emailLogDetail(id ?? 0),
    queryFn: () => fetchEmailLogDetail(id ?? 0),
    enabled: id !== null,
    staleTime: Infinity,
  })
}
