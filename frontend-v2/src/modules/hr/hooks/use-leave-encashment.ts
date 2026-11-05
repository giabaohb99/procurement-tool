import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { appConfig } from '@/core/config/app-config'
import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { leaveEncashmentApi, type LeaveEncashmentPreviewParams } from '../api/leave-encashment-api'
import type {
  LeaveEncashmentAction,
  LeaveEncashmentCreatePayload,
  LeaveEncashmentUpdatePayload,
} from '../types/leave-encashment'

/**
 * Hook của Phiếu thanh toán nghỉ phép (duoc-CR-719). Khuôn `use-leave-comp.ts`.
 *
 * ⚠️ Mọi mutation dọn `queryKeys.hr.all` (duyệt / hủy đổi `encashed_days` của quỹ phép — bảng quỹ, thẻ quỹ và ô
 * "Số được thanh toán" phải nạp lại), `approval.all` (gửi duyệt mở phiên, hủy rút phiên) và `finance.all` (duyệt sinh
 * YCTT, hủy xóa YCTT Nháp — danh sách YCTT phải thấy ngay).
 */

export function useLeaveEncashments(params: ListParams = {}, options: { enabled?: boolean } = {}) {
  const query: ListParams = { page: 1, page_size: appConfig.defaultPageSize, ...params }
  return useQuery({
    queryKey: queryKeys.hr.leaveEncashments(query),
    queryFn: () => leaveEncashmentApi.list(query),
    placeholderData: keepPreviousData,
    enabled: options.enabled ?? true,
  })
}

/** ⚠️ `staleTime: 0`: hàng đợi việc, một dòng đã bị người khác xử lý mà còn nằm đó là bấm ăn lỗi. */
export function useLeaveEncashmentToApprove(enabled = true) {
  return useQuery({
    queryKey: queryKeys.hr.leaveEncashmentToApprove(),
    queryFn: () => leaveEncashmentApi.listToApprove(),
    staleTime: 0,
    enabled,
  })
}

export function useLeaveEncashment(id: number) {
  return useQuery({
    queryKey: queryKeys.hr.leaveEncashment(id),
    queryFn: () => leaveEncashmentApi.get(id),
    enabled: id > 0,
  })
}

/**
 * Số ngày được thanh toán của (người, loại, năm, lý do). Chỉ gọi khi đã chọn loại nghỉ.
 * `retry: false`: 422 (thiếu ngày nghỉ việc, quỹ năm trước chưa có…) là câu trả lời, không phải lỗi mạng — gọi lại
 * ba lần là ba toast giống nhau.
 */
export function useLeaveEncashmentPreview(params: LeaveEncashmentPreviewParams, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.hr.leaveEncashmentPreview({ ...params }),
    queryFn: () => leaveEncashmentApi.preview(params),
    enabled: enabled && params.leave_type_id > 0,
    retry: false,
  })
}

function useInvalidateAfterChange() {
  const queryClient = useQueryClient()
  return () => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    void queryClient.invalidateQueries({ queryKey: queryKeys.approval.all })
    void queryClient.invalidateQueries({ queryKey: queryKeys.finance.all })
  }
}

export function useSaveLeaveEncashment() {
  const invalidate = useInvalidateAfterChange()
  return useMutation({
    mutationFn: (
      input:
        | { id: number; values: LeaveEncashmentUpdatePayload }
        | { id?: undefined; values: LeaveEncashmentCreatePayload },
    ) =>
      input.id
        ? leaveEncashmentApi.update(input.id, input.values)
        : leaveEncashmentApi.create(input.values as LeaveEncashmentCreatePayload),
    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã cập nhật phiếu thanh toán nghỉ phép' : 'Đã lưu nháp phiếu thanh toán nghỉ phép')
      invalidate()
    },
  })
}

export function useDeleteLeaveEncashment() {
  const invalidate = useInvalidateAfterChange()
  return useMutation({
    mutationFn: (id: number) => leaveEncashmentApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa phiếu thanh toán nghỉ phép')
      invalidate()
    },
  })
}

const ACTION_MESSAGES: Record<LeaveEncashmentAction, string> = {
  submit: 'Đã gửi duyệt phiếu thanh toán nghỉ phép',
  approve: 'Đã duyệt phiếu — đã tạo yêu cầu thanh toán cho kế toán',
  reject: 'Đã từ chối phiếu thanh toán nghỉ phép',
  cancel: 'Đã hủy phiếu thanh toán nghỉ phép',
}

/** Bốn thao tác đổi trạng thái gộp một hook — cùng khuôn `useLeaveCompAction`. */
export function useLeaveEncashmentAction() {
  const invalidate = useInvalidateAfterChange()
  return useMutation({
    mutationFn: ({ id, action, reason }: { id: number; action: LeaveEncashmentAction; reason?: string }) => {
      if (action === 'submit') return leaveEncashmentApi.submit(id)
      if (action === 'approve') return leaveEncashmentApi.approve(id)
      if (action === 'reject') return leaveEncashmentApi.reject(id, reason ?? '')
      return leaveEncashmentApi.cancel(id, reason ?? '')
    },
    onSuccess: (_data, variables) => {
      toast.success(ACTION_MESSAGES[variables.action])
      invalidate()
    },
  })
}
