import { useMutation, useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { useAuthStore } from '@/core/auth/auth-store'
import { queryKeys } from '@/shared/constants/query-keys'
import {
  deleteWorkHistoryFile,
  fetchWorkHistoryFiles,
  uploadWorkHistoryFiles,
} from '../api/employee-work-history-api'
import type { WorkHistoryFile } from '../types/employee-work-history'

/**
 * Tệp QĐ của MỘT dòng quá trình công tác (A6). Dòng chưa lưu (`id = 0`) hoặc
 * hộp chưa mở (`enabled=false`) thì không gọi — tránh gọi `/api/attachments`
 * khi người xem không có quyền mở tệp (Q4, xem `employee-tab-work-history.tsx`).
 */
export function useWorkHistoryFiles(historyId: number, enabled = true) {
  return useQuery({
    queryKey: queryKeys.hr.workHistoryFiles(historyId),
    queryFn: () => fetchWorkHistoryFiles(historyId),
    enabled: historyId > 0 && enabled,
  })
}

/**
 * Dọn cache sau khi tải lên / gỡ tệp — phát hiện lúc kiểm tay bằng Chrome
 * DevTools 03/10/2026: hộp tệp trước đây CHỈ dọn `workHistoryFiles(historyId)`
 * của chính nó, nên cột «Tệp» ở bảng ngoài (đọc `file_count` từ
 * `employeeWorkHistory(eid)` / `myWorkHistory()`) đứng ở số cũ tới khi bấm
 * «Tải lại dữ liệu». `employeeId` là id hồ sơ CHỦ của dòng lịch sử (nơi gọi
 * luôn biết — xem `employee-work-history-files-dialog.tsx`), không phải id
 * người đang xem.
 */
function invalidateWorkHistoryLists(
  queryClient: QueryClient,
  historyId: number,
  employeeId: number,
) {
  void queryClient.invalidateQueries({ queryKey: queryKeys.hr.workHistoryFiles(historyId) })
  void queryClient.invalidateQueries({ queryKey: queryKeys.hr.employeeWorkHistory(employeeId) })

  const currentUser = useAuthStore.getState().user
  if (employeeId > 0 && currentUser?.employee_id === employeeId) {
    void queryClient.invalidateQueries({ queryKey: queryKeys.hr.myWorkHistory() })
  }
}

export function useUploadWorkHistoryFiles(historyId: number, employeeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (files: File[]) => uploadWorkHistoryFiles(historyId, files),
    onSuccess: (uploaded: WorkHistoryFile[]) => {
      toast.success(uploaded.length > 1 ? `Đã tải lên ${uploaded.length} tệp` : 'Đã tải lên tệp')
      invalidateWorkHistoryLists(queryClient, historyId, employeeId)
    },
    //  KHÔNG khai `onError`: `httpClient` đã tự bày toast cho mọi lệnh khác GET.
  })
}

export function useDeleteWorkHistoryFile(historyId: number, employeeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (linkId: number) => deleteWorkHistoryFile(linkId),
    onSuccess: () => {
      toast.success('Đã gỡ tệp')
      invalidateWorkHistoryLists(queryClient, historyId, employeeId)
    },
  })
}
