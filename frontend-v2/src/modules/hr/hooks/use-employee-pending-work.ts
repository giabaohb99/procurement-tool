import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { approvalApi } from '@/modules/approval/api/approval-api'
import { queryKeys } from '@/shared/constants/query-keys'
import { employeeApi } from '../api/employee-api'

/** Khóa nằm DƯỚI `hr.all` nên mọi lần `invalidate(hr.all)` (khóa tài khoản, lưu hồ sơ) làm mới luôn. */
const pendingWorkKey = (employeeId: number) =>
  [...queryKeys.hr.all, 'employee-pending-work', employeeId] as const

/**
 * Việc duyệt đang treo của một nhân sự (duoc-CR-665).
 * `staleTime: 0` + không cache lâu: danh sách này quyết định có khóa tài khoản hay không,
 * đọc bản cũ là cảnh báo sai.
 */
export function useEmployeePendingWork(employeeId: number, enabled = true) {
  return useQuery({
    queryKey: pendingWorkKey(employeeId),
    queryFn: () => employeeApi.pendingWork(employeeId),
    enabled: enabled && employeeId > 0,
    staleTime: 0,
    gcTime: 0,
    retry: false,
  })
}

/** Chuyển MỘT việc (đường có sẵn `PATCH /api/approvals/tasks/{id}/reassign`). */
export function useReassignPendingTask(employeeId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ taskId, toEmployeeId }: { taskId: number; toEmployeeId: number }) =>
      approvalApi.reassign(taskId, toEmployeeId, 'Bàn giao trước khi khóa tài khoản'),
    onSuccess: () => {
      toast.success('Đã chuyển việc')
      void queryClient.invalidateQueries({ queryKey: pendingWorkKey(employeeId) })
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}

/** Chuyển HẾT việc đang treo (`POST /api/approvals/handover`) — việc không chuyển được vẫn còn trong danh sách. */
export function useHandoverAllPendingTasks(employeeId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ toEmployeeId }: { toEmployeeId: number }) =>
      approvalApi.handover(employeeId, toEmployeeId, 'Bàn giao trước khi khóa tài khoản'),
    onSuccess: (result) => {
      toast.success(`Đã chuyển ${result.count} việc`)
      void queryClient.invalidateQueries({ queryKey: pendingWorkKey(employeeId) })
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}
