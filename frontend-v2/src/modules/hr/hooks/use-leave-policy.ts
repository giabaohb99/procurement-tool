import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { appConfig } from '@/core/config/app-config'
import { queryKeys } from '@/shared/constants/query-keys'
import { useCrudList } from '@/shared/crud'
import type { ListParams } from '@/shared/types/api'
import { leavePolicyApi } from '../api/leave-policy-api'
import type {
  LeavePolicy,
  LeavePolicyLine,
  PolicyAssignPayload,
  PolicyAssignmentUpdatePayload,
  PolicyBulkPayload,
  PolicyPreviewPayload,
} from '../types/leave-policy'
import { describeBalanceChanges } from '../utils/leave-policy-display'

/**
 * Hook của Chính sách nghỉ phép + Phân bổ chính sách (duoc-CR-717).
 *
 * ⚠️ Mọi mutation PHÂN BỔ dọn `queryKeys.hr.all`: phân bổ có tick "Tính lại" đổi `allocated_days`
 * của quỹ năm nay, nên danh sách quỹ, chi tiết dòng quỹ, ma trận theo nhân sự và ô gợi ý số phép
 * trên form đơn nghỉ đều phải nạp lại. Dọn lẻ là chắc chắn có màn hiện số cũ.
 */

/**
 * Gói ĐANG DÙNG cho ô chọn ở hộp phân bổ / trang hàng loạt — đi chung cache CRUD (`['crud', apiPath]`)
 * nên thêm / sửa / ngừng gói ở màn Thiết lập là ô chọn tự làm mới. Đọc cần `leave_type.read`; thiếu
 * quyền thì GET lỗi êm (http client chỉ bật toast cho lệnh ghi) và ô chọn rỗng.
 */
export function useActiveLeavePolicies() {
  return useCrudList<LeavePolicy>('/api/leave-policies', {
    page_size: 200,
    is_active: 'true',
    sort_by: 'name',
    sort_dir: 'asc',
  })
}

export function useLeavePolicyLines(policyId: number, enabled = true) {
  return useQuery({
    queryKey: queryKeys.hr.leavePolicyLines(policyId),
    queryFn: () => leavePolicyApi.listLines(policyId),
    enabled: enabled && policyId > 0,
  })
}

export function useReplaceLeavePolicyLines(policyId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (items: LeavePolicyLine[]) => leavePolicyApi.replaceLines(policyId, items),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.hr.leavePolicyLines(policyId), data)
      //  Hộp phân bổ đang mở xem trước theo dòng cũ — dọn GỐC (cả danh sách lẫn xem trước) để lần xem
      //  kế tiếp đọc dòng mới. Dọn `leavePolicyAssignments()` thì trượt khóa xem trước (review L1).
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.leavePolicyAssignmentsRoot })
      toast.success('Đã lưu loại nghỉ & số ngày của chính sách')
    },
  })
}

export function useLeavePolicyAssignments(
  params: ListParams = {},
  options: { enabled?: boolean } = {},
) {
  const query: ListParams = { page: 1, page_size: appConfig.defaultPageSize, ...params }
  return useQuery({
    queryKey: queryKeys.hr.leavePolicyAssignments(query),
    queryFn: () => leavePolicyApi.listAssignments(query),
    placeholderData: keepPreviousData,
    enabled: options.enabled ?? true,
  })
}

/**
 * Xem trước cho hộp phân bổ MỘT người: chạy lại mỗi khi bộ tham số đổi. `staleTime: 0` — số trước →
 * sau phải là số của lúc bấm Lưu, không phải của nửa phút trước.
 */
export function useLeavePolicyPreview(payload: PolicyPreviewPayload | null) {
  return useQuery({
    queryKey: queryKeys.hr.leavePolicyPreview({ ...(payload ?? {}) }),
    queryFn: () => leavePolicyApi.preview(payload as PolicyPreviewPayload),
    enabled: payload !== null,
    staleTime: 0,
  })
}

/** Xem trước cho trang HÀNG LOẠT — chạy khi bấm "Xem danh sách", không tự chạy theo từng ô lọc. */
export function useLeavePolicyBulkPreview() {
  return useMutation({ mutationFn: (payload: PolicyPreviewPayload) => leavePolicyApi.preview(payload) })
}

function useInvalidateLeaveData() {
  const queryClient = useQueryClient()
  return () => void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
}

export function useCreateLeavePolicyAssignment() {
  const invalidate = useInvalidateLeaveData()
  return useMutation({
    mutationFn: (payload: PolicyAssignPayload) => leavePolicyApi.create(payload),
    onSuccess: (data) => {
      toast.success('Đã phân bổ chính sách', { description: describeBalanceChanges(data.balances) })
      invalidate()
    },
  })
}

export function useBulkLeavePolicyAssignment() {
  const invalidate = useInvalidateLeaveData()
  return useMutation({
    mutationFn: (payload: PolicyBulkPayload) => leavePolicyApi.bulk(payload),
    onSuccess: () => invalidate(),
  })
}

export function useUpdateLeavePolicyAssignment() {
  const invalidate = useInvalidateLeaveData()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: PolicyAssignmentUpdatePayload }) =>
      leavePolicyApi.update(id, payload),
    onSuccess: (data) => {
      toast.success('Đã cập nhật phân bổ', { description: describeBalanceChanges(data.balances) })
      invalidate()
    },
  })
}

export function useDeleteLeavePolicyAssignment() {
  const invalidate = useInvalidateLeaveData()
  return useMutation({
    mutationFn: ({ id, recalc }: { id: number; recalc: boolean }) => leavePolicyApi.remove(id, recalc),
    onSuccess: (data) => {
      toast.success('Đã xóa phân bổ', { description: describeBalanceChanges(data.balances) })
      invalidate()
    },
  })
}
