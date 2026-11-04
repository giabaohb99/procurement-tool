import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { appConfig } from '@/core/config/app-config'
import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { leaveCompApi } from '../api/leave-comp-api'
import type { LeaveCompAction, LeaveCompPayload } from '../types/leave-comp'

/**
 * Hook của Phiếu xin nghỉ bù (duoc-CR-715 phase C).
 *
 * ⚠️ Mọi mutation dọn `queryKeys.hr.all`: duyệt / hủy phiếu đổi `comp_days` của quỹ phép nên
 * danh sách quỹ, thẻ "Quỹ phép của tôi" và ô gợi ý trên form đơn nghỉ đều phải nạp lại.
 * Cũng dọn `approval.all` — gửi duyệt mở phiên, hủy thì rút phiên.
 */

export function useLeaveCompRequests(params: ListParams = {}, options: { enabled?: boolean } = {}) {
  const query: ListParams = { page: 1, page_size: appConfig.defaultPageSize, ...params }
  return useQuery({
    queryKey: queryKeys.hr.leaveCompRequests(query),
    queryFn: () => leaveCompApi.list(query),
    placeholderData: keepPreviousData,
    enabled: options.enabled ?? true,
  })
}

/** ⚠️ `staleTime: 0`: hàng đợi việc, một dòng đã bị người khác xử lý mà còn nằm đó là bấm ăn lỗi. */
export function useLeaveCompToApprove(enabled = true) {
  return useQuery({
    queryKey: queryKeys.hr.leaveCompToApprove(),
    queryFn: () => leaveCompApi.listToApprove(),
    staleTime: 0,
    enabled,
  })
}

export function useLeaveCompRequest(id: number) {
  return useQuery({
    queryKey: queryKeys.hr.leaveCompRequest(id),
    queryFn: () => leaveCompApi.get(id),
    enabled: id > 0,
  })
}

function useInvalidateAfterChange() {
  const queryClient = useQueryClient()
  return () => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    void queryClient.invalidateQueries({ queryKey: queryKeys.approval.all })
  }
}

export function useSaveLeaveCompRequest() {
  const invalidate = useInvalidateAfterChange()
  return useMutation({
    mutationFn: ({ id, values }: { id?: number; values: LeaveCompPayload }) =>
      id ? leaveCompApi.update(id, values) : leaveCompApi.create(values),
    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã cập nhật phiếu nghỉ bù' : 'Đã lưu nháp phiếu nghỉ bù')
      invalidate()
    },
  })
}

export function useDeleteLeaveCompRequest() {
  const invalidate = useInvalidateAfterChange()
  return useMutation({
    mutationFn: (id: number) => leaveCompApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa phiếu nghỉ bù')
      invalidate()
    },
  })
}

const ACTION_MESSAGES: Record<LeaveCompAction, string> = {
  submit: 'Đã gửi duyệt phiếu nghỉ bù',
  approve: 'Đã duyệt phiếu nghỉ bù',
  reject: 'Đã từ chối phiếu nghỉ bù',
  cancel: 'Đã hủy phiếu nghỉ bù',
}

/** Bốn thao tác đổi trạng thái gộp một hook — cùng khuôn `useLeaveRequestAction`. */
export function useLeaveCompAction() {
  const invalidate = useInvalidateAfterChange()
  return useMutation({
    mutationFn: ({ id, action, reason }: { id: number; action: LeaveCompAction; reason?: string }) => {
      if (action === 'submit') return leaveCompApi.submit(id)
      if (action === 'approve') return leaveCompApi.approve(id)
      if (action === 'reject') return leaveCompApi.reject(id, reason ?? '')
      return leaveCompApi.cancel(id, reason ?? '')
    },
    onSuccess: (_data, variables) => {
      toast.success(ACTION_MESSAGES[variables.action])
      invalidate()
    },
  })
}
