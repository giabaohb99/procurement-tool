import { useMutation, useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { employeeChangeRequestApi } from '../api/employee-change-request-api'
import type { ChangeRequestPayload } from '../types/employee-change-request'

/**
 * Hook của ĐỀ NGHỊ SỬA HỒ SƠ (duoc-CR-676).
 *
 * ⚠️ Cửa phía phòng Nhân sự trả 403 khi thiếu `employee.write` — nơi gọi PHẢI truyền `enabled`
 * (huy hiệu menu, dải báo trên màn hồ sơ), không thì cứ mount là bắn và người dùng thấy lỗi.
 */

/** Hộ gia đình của chính mình. Tắt khi tài khoản chưa gắn hồ sơ (cửa `/me/*` trả 400). */
export function useMyFamilies(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.hr.myEmployeeFamilies(),
    queryFn: () => employeeChangeRequestApi.getMyFamilies(),
    enabled,
  })
}

export function useMyChangeRequests(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.hr.myChangeRequests(),
    queryFn: () => employeeChangeRequestApi.listMine(),
    enabled,
  })
}

/** Phía nhân viên đổi trạng thái một đề nghị → nạp lại danh sách của tôi + mọi màn duyệt. */
function invalidateAfterSelfAction(queryClient: QueryClient) {
  return Promise.all([
    queryClient.invalidateQueries({ queryKey: queryKeys.hr.myChangeRequests() }),
    queryClient.invalidateQueries({ queryKey: queryKeys.hr.changeRequestsRoot() }),
  ])
}

export function useSubmitMyChangeRequest() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: ChangeRequestPayload) => employeeChangeRequestApi.submitMine(payload),
    onSuccess: () => {
      toast.success('Đã gửi đề nghị. Phòng Nhân sự duyệt xong mới cập nhật vào hồ sơ.')
      void invalidateAfterSelfAction(queryClient)
    },
  })
}

export function useWithdrawMyChangeRequest() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => employeeChangeRequestApi.withdrawMine(id),
    onSuccess: () => {
      toast.success('Đã rút đề nghị')
      void invalidateAfterSelfAction(queryClient)
    },
  })
}

export function useChangeRequests(params: ListParams, enabled = true) {
  return useQuery({
    queryKey: queryKeys.hr.changeRequests(params),
    queryFn: () => employeeChangeRequestApi.list(params),
    enabled,
  })
}

/** Số đề nghị đang chờ — huy hiệu menu "Duyệt sửa hồ sơ". */
export function useChangeRequestPendingCount(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.hr.changeRequestPendingCount(),
    queryFn: () => employeeChangeRequestApi.pendingCount(),
    enabled,
    //  Không cần thời gian thực: huy hiệu nhắc "còn việc", trễ một phút không ai thiệt.
    staleTime: 60_000,
  })
}

export function useChangeRequest(id: number) {
  return useQuery({
    queryKey: queryKeys.hr.changeRequest(id),
    queryFn: () => employeeChangeRequestApi.getById(id),
    enabled: id > 0,
  })
}

/**
 * Duyệt / từ chối xong: nạp lại danh sách + số đếm + chi tiết (chung gốc `changeRequestsRoot`),
 * hồ sơ của người được duyệt (khóa cha quét luôn hộ gia đình), các trang danh sách nhân sự, và
 * hai khóa "của tôi" — admin được duyệt đề nghị của CHÍNH MÌNH (review L3), Trang cá nhân phải
 * thấy ngay. `myEmployee` (`['hr','employees','me']`) KHÔNG khớp `employees()` (`{}` ≠ `'me'`).
 */
function invalidateAfterDecision(queryClient: QueryClient, employeeId: number) {
  return Promise.all([
    queryClient.invalidateQueries({ queryKey: queryKeys.hr.changeRequestsRoot() }),
    queryClient.invalidateQueries({ queryKey: queryKeys.hr.employee(employeeId) }),
    queryClient.invalidateQueries({ queryKey: queryKeys.hr.employees() }),
    queryClient.invalidateQueries({ queryKey: queryKeys.hr.myEmployee() }),
    queryClient.invalidateQueries({ queryKey: queryKeys.hr.myChangeRequests() }),
  ])
}

/** Duyệt / từ chối hỏng (409: người khác vừa xử lý, hộ gia đình đổi sau lúc gửi) → nạp lại chi tiết. */
function refreshAfterDecisionError(queryClient: QueryClient) {
  return queryClient.invalidateQueries({ queryKey: queryKeys.hr.changeRequestsRoot() })
}

export function useApproveChangeRequest(employeeId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => employeeChangeRequestApi.approve(id),
    onSuccess: () => {
      toast.success('Đã duyệt và cập nhật vào hồ sơ')
      void invalidateAfterDecision(queryClient, employeeId)
    },
    onError: () => void refreshAfterDecisionError(queryClient),
  })
}

export function useRejectChangeRequest(employeeId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) =>
      employeeChangeRequestApi.reject(id, reason),
    onSuccess: () => {
      toast.success('Đã từ chối đề nghị')
      void invalidateAfterDecision(queryClient, employeeId)
    },
    onError: () => void refreshAfterDecisionError(queryClient),
  })
}
