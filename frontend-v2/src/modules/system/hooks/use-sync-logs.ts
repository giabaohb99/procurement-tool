import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import {
  fetchSyncLogDetail,
  fetchSyncLogMeta,
  fetchSyncLogStats,
  fetchSyncLogs,
  retrySyncLog,
  type SyncLogFilters,
} from '../api/sync-log-api'

/** Danh sách dòng sổ đồng bộ, mới nhất trước. */
export function useSyncLogs(params: SyncLogFilters) {
  return useQuery({
    queryKey: queryKeys.system.syncLogs(params as Record<string, unknown>),
    queryFn: () => fetchSyncLogs(params),
    placeholderData: keepPreviousData,
    staleTime: 10 * 1000,
  })
}

/**
 * Bộ chọn cho các ô lọc.
 *
 * `staleTime: Infinity` — danh sách nguồn / đối tượng / cờ cảnh báo chỉ đổi khi
 * ai đó khai thêm hệ nguồn trong mã nguồn, tức là sau một lần deploy. Trong một
 * phiên làm việc nó là hằng số.
 */
export function useSyncLogMeta() {
  return useQuery({
    queryKey: queryKeys.system.syncLogMeta(),
    queryFn: fetchSyncLogMeta,
    staleTime: Infinity,
  })
}

/** Thẻ đếm theo trạng thái trong N ngày gần đây. */
export function useSyncLogStats(params: { source?: string; days?: number }) {
  return useQuery({
    queryKey: queryKeys.system.syncLogStats(params as Record<string, unknown>),
    queryFn: () => fetchSyncLogStats(params),
    placeholderData: keepPreviousData,
    staleTime: 30 * 1000,
  })
}

/**
 * Một dòng kèm nguyên cục dữ liệu bên kia gửi sang.
 *
 * `staleTime: Infinity` — một dòng sổ đã đóng thì không bao giờ đổi nữa (luật
 * §3.2: một dòng = một sự kiện, không ghi đè). Dòng *chờ* / *đang chạy* thì có
 * đổi, nhưng đóng ngăn rồi mở lại là nạp mới, đủ cho việc đi tra sự cố.
 */
export function useSyncLogDetail(id: number | null) {
  return useQuery({
    queryKey: queryKeys.system.syncLogDetail(id ?? 0),
    queryFn: () => fetchSyncLogDetail(id ?? 0),
    enabled: id !== null,
    staleTime: Infinity,
  })
}

/**
 * Xếp hàng chạy lại một dòng hỏng — cần `sync_log.write`.
 *
 * Toast nói rõ là ĐÃ XẾP HÀNG chứ không phải đã chạy xong: dòng mới nằm ở trạng
 * thái *chờ* cho tới khi vòng chạy nền của hệ nguồn nhặt lên (app đặt xe cũ:
 * `datxe.retry_pending`, mỗi 10 phút ở các phút lẻ 3, 13, 23…). Không nói rõ
 * thì người ta bấm xong nhìn bảng, thấy dòng cũ vẫn *lỗi*, rồi bấm tiếp năm lần.
 */
export function useRetrySyncLog() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => retrySyncLog(id),
    onSuccess: (fresh) => {
      toast.success(
        `Đã xếp hàng chạy lại (dòng mới #${fresh?.id ?? '?'}). ` +
          'Vòng chạy nền của hệ nguồn sẽ nhặt trong ít phút tới.',
      )
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.syncLogs() })
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.syncLogStats() })
    },
  })
}
