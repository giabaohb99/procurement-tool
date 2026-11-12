import { useMutation, useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import {
  deleteConcurrentFile,
  fetchConcurrentFiles,
  uploadConcurrentFiles,
} from '../api/employee-concurrent-api'
import type { WorkHistoryFile } from '../types/employee-work-history'

/**
 * Tệp QĐ của MỘT dòng kiêm nhiệm. Hộp chưa mở (`enabled=false`) thì không gọi — người không được mở tệp
 * (`can_open_files=false`) không bao giờ chạm tới `/api/attachments`.
 */
export function useConcurrentFiles(concurrentId: number, enabled = true) {
  return useQuery({
    queryKey: queryKeys.hr.concurrentFiles(concurrentId),
    queryFn: () => fetchConcurrentFiles(concurrentId),
    enabled: concurrentId > 0 && enabled,
  })
}

/** Cột "Tệp" của bảng đọc `file_count` từ danh sách dòng — tải/gỡ tệp xong phải nạp lại cả danh sách đó. */
function invalidateConcurrentFiles(queryClient: QueryClient, concurrentId: number, employeeId: number) {
  void queryClient.invalidateQueries({ queryKey: queryKeys.hr.concurrentFiles(concurrentId) })
  void queryClient.invalidateQueries({ queryKey: queryKeys.hr.employeeConcurrents(employeeId) })
}

export function useUploadConcurrentFiles(concurrentId: number, employeeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (files: File[]) => uploadConcurrentFiles(concurrentId, files),
    onSuccess: (uploaded: WorkHistoryFile[]) => {
      toast.success(uploaded.length > 1 ? `Đã tải lên ${uploaded.length} tệp` : 'Đã tải lên tệp')
      invalidateConcurrentFiles(queryClient, concurrentId, employeeId)
    },
  })
}

export function useDeleteConcurrentFile(concurrentId: number, employeeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (linkId: number) => deleteConcurrentFile(linkId),
    onSuccess: () => {
      toast.success('Đã gỡ tệp')
      invalidateConcurrentFiles(queryClient, concurrentId, employeeId)
    },
  })
}
