import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import {
  fetchEmailLogDetail,
  fetchEmailLogMeta,
  fetchEmailLogStats,
  fetchEmailLogs,
  resendEmailLog,
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

/**
 * Gửi lại một thư (bao-CR-727) — cần `audit.write`.
 *
 * Toast nói rõ là ĐÃ XẾP GỬI và chỉ ra dòng mới: dòng cũ giữ nguyên trạng thái (vd *Lỗi*), người ta phải nhìn
 * dòng mới để biết lần này tới chưa. Lỗi (400 thư không lưu nội dung, 429 bấm liên tục) do http-client toast sẵn.
 */
export function useResendEmailLog() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => resendEmailLog(id),
    onSuccess: (fresh) => {
      toast.success(`Đã xếp gửi lại thư tới ${fresh?.to_email ?? ''} (dòng mới #${fresh?.id ?? '?'}).`)
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.emailLogs() })
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.emailLogStats(7) })
    },
  })
}
