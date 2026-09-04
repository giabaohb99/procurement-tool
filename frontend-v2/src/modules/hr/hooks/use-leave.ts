import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { appConfig } from '@/core/config/app-config'
import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { leaveApi, type LeaveRequestPayload } from '../api/leave-api'

/**
 * Hook của phân hệ Nghỉ phép (CR-259).
 *
 * ⚠️ Mọi mutation đều dọn `queryKeys.hr.all`, không dọn lẻ từng khóa. Lý do:
 * **số phép còn lại xuất hiện ở ba màn** — ô gợi ý trên form nộp đơn, thẻ «Quỹ
 * phép của tôi», và bảng Quỹ phép của Nhân sự. Duyệt một đơn là cả ba đổi. Dọn
 * lẻ thì chắc chắn có màn hiện số cũ, và số cũ ở đây nghĩa là người ta tưởng
 * mình còn phép.
 */

// ── Đơn nghỉ phép ──────────────────────────────────────────────────────────────

export function useLeaveRequests(params: ListParams = {}, options: { enabled?: boolean } = {}) {
  const query: ListParams = { page: 1, page_size: appConfig.defaultPageSize, ...params }
  return useQuery({
    queryKey: queryKeys.hr.leaveRequests(query),
    queryFn: () => leaveApi.listRequests(query),
    placeholderData: keepPreviousData,
    enabled: options.enabled ?? true,
  })
}

export function useLeaveRequest(id: number) {
  return useQuery({
    queryKey: queryKeys.hr.leaveRequest(id),
    queryFn: () => leaveApi.getRequest(id),
    enabled: id > 0,
  })
}

export function useSaveLeaveRequest() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, values }: { id?: number; values: LeaveRequestPayload }) =>
      id ? leaveApi.updateRequest(id, values) : leaveApi.createRequest(values),
    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã cập nhật đơn' : 'Đã lưu đơn nghỉ phép')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

export function useDeleteLeaveRequest() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => leaveApi.removeRequest(id),
    onSuccess: () => {
      toast.success('Đã xóa đơn')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

/**
 * Bốn thao tác đổi trạng thái gộp một hook.
 *
 * Gộp vì cả bốn làm đúng một việc với cache (dọn `hr.all`) và khác nhau đúng
 * một câu thông báo. Tách bốn hook là bốn bản chép của cùng một `onSuccess`, và
 * sớm muộn có bản quên dòng `invalidateQueries`.
 */
export type LeaveAction = 'submit' | 'approve' | 'reject' | 'cancel'

const ACTION_MESSAGES: Record<LeaveAction, string> = {
  submit: 'Đã gửi duyệt',
  approve: 'Đã duyệt đơn',
  reject: 'Đã từ chối đơn',
  cancel: 'Đã hủy đơn',
}

export function useLeaveRequestAction() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, action, reason }: { id: number; action: LeaveAction; reason?: string }) => {
      if (action === 'submit') return leaveApi.submitRequest(id)
      if (action === 'approve') return leaveApi.approveRequest(id)
      if (action === 'reject') return leaveApi.rejectRequest(id, reason ?? '')
      return leaveApi.cancelRequest(id, reason ?? '')
    },
    onSuccess: (_data, variables) => {
      toast.success(ACTION_MESSAGES[variables.action])
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

// ── Hai ô trợ giúp trên FORM ───────────────────────────────────────────────────

/** Số ngày gợi ý. Chỉ chạy khi đã đủ hai đầu ngày — thiếu là backend trả 422. */
export function useEstimateLeaveDays(params: {
  from_date: string
  to_date: string
  leave_type_id?: number
  from_session?: number
  to_session?: number
  employee_id?: number
}) {
  const ready = Boolean(params.from_date && params.to_date)
  return useQuery({
    queryKey: ['hr', 'leave-estimate', params] as const,
    queryFn: () => leaveApi.estimateDays(params),
    enabled: ready,
  })
}

/** Số phép còn lại — ràng buộc §6.1 của kế hoạch. Chưa chọn loại nghỉ thì không gọi. */
export function useLeaveBalanceHint(leaveTypeId: number, year: number, employeeId = 0) {
  return useQuery({
    queryKey: queryKeys.hr.leaveBalanceHint(employeeId, leaveTypeId, year),
    queryFn: () =>
      leaveApi.balanceHint({
        leave_type_id: leaveTypeId,
        year,
        ...(employeeId ? { employee_id: employeeId } : {}),
      }),
    enabled: leaveTypeId > 0,
  })
}

// ── Quỹ phép ───────────────────────────────────────────────────────────────────

export function useLeaveBalances(params: ListParams = {}, options: { enabled?: boolean } = {}) {
  const query: ListParams = { page: 1, page_size: appConfig.defaultPageSize, ...params }
  return useQuery({
    queryKey: queryKeys.hr.leaveBalances(query),
    queryFn: () => leaveApi.listBalances(query),
    placeholderData: keepPreviousData,
    enabled: options.enabled ?? true,
  })
}

/** Một dòng quỹ — trang chi tiết `/hr/leave-balances/:id`. */
export function useLeaveBalance(id: number) {
  return useQuery({
    queryKey: queryKeys.hr.leaveBalance(id),
    queryFn: () => leaveApi.getBalance(id),
    enabled: id > 0,
  })
}

/** Toàn bộ quỹ của MỘT người trong một năm — thẻ «Quỹ phép của tôi». */
export function useLeaveBalanceSummary(employeeId: number, year: number, enabled = true) {
  return useQuery({
    queryKey: queryKeys.hr.leaveBalanceSummary(employeeId, year),
    queryFn: () =>
      leaveApi.balanceSummary({ ...(employeeId ? { employee_id: employeeId } : {}), year }),
    enabled,
  })
}

export function useAdjustLeaveBalance() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, values }: { id: number; values: { adjusted_days: number; note: string } }) =>
      leaveApi.adjustBalance(id, values),
    onSuccess: () => {
      toast.success('Đã điều chỉnh quỹ phép')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

export function useAllocateLeaveBalance() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (values: { year: number; leave_type_ids?: number[]; employee_ids?: number[] }) =>
      leaveApi.allocate(values),
    onSuccess: (data) => {
      toast.success(`Đã cấp quỹ phép năm ${data.year} — thêm ${data.created} dòng`)
      //  Q4 — nói thẳng ra ai chưa có ngày vào làm. Những người này được cấp quỹ
      //  với thâm niên 0, tức là THIẾU ngày nếu họ đã làm lâu năm. Im lặng ở đây
      //  là để sai số nằm trong sổ cả năm không ai biết.
      if (data.missing_hire_date_count > 0) {
        toast.warning(
          `${data.missing_hire_date_count} nhân sự chưa có ngày vào làm — quỹ của họ ` +
            'tính thâm niên bằng 0. Nhập ngày vào làm rồi chỉnh tay phần thiếu.',
        )
      }
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

// ── Danh mục nền ───────────────────────────────────────────────────────────────

/** Loại nghỉ đang dùng — nạp cả danh sách, dùng cho ô chọn trên form. */
export function useLeaveTypes(activeOnly = true) {
  const params: ListParams = { page: 1, page_size: 200 }
  if (activeOnly) params.is_active = 'true'
  return useQuery({
    queryKey: queryKeys.hr.leaveTypes(params),
    queryFn: () => leaveApi.listTypes(params),
  })
}

export function useSeniorityTiers(leaveTypeId: number) {
  return useQuery({
    queryKey: queryKeys.hr.seniorityTiers(leaveTypeId),
    queryFn: () => leaveApi.listTiers(leaveTypeId),
    enabled: leaveTypeId > 0,
  })
}

export function useSaveSeniorityTier(leaveTypeId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      values,
    }: {
      id?: number
      values: { years_from: number; years_to: number; extra_days: number; note?: string }
    }) =>
      id
        ? leaveApi.updateTier(id, values)
        : leaveApi.createTier({ leave_type_id: leaveTypeId, note: '', ...values }),
    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã cập nhật bậc' : 'Đã thêm bậc thâm niên')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.seniorityTiers(leaveTypeId) })
    },
  })
}

export function useDeleteSeniorityTier(leaveTypeId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => leaveApi.removeTier(id),
    onSuccess: () => {
      toast.success('Đã xóa bậc')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.seniorityTiers(leaveTypeId) })
    },
  })
}

// ── Hộp việc duyệt (CR-260) ────────────────────────────────────────────────────

/**
 * Đơn ĐANG chờ chính tôi ký.
 *
 * ⚠️ `staleTime: 0` cố ý: đây là hàng đợi công việc, và một dòng đã bị người
 * khác xử lý mà vẫn nằm đó thì người dùng bấm Duyệt rồi ăn lỗi "không có việc
 * nào đang chờ". Danh sách đơn thường thì cũ vài giây không sao, hàng đợi thì
 * có.
 */
export function useLeaveToApprove(enabled = true) {
  return useQuery({
    queryKey: queryKeys.hr.leaveToApprove(),
    queryFn: () => leaveApi.listToApprove(),
    staleTime: 0,
    enabled,
  })
}

/** Đơn chính tôi vừa quyết định gần đây. */
export function useLeaveHandled(params: { days?: number; limit?: number } = {},
                                enabled = true) {
  return useQuery({
    queryKey: queryKeys.hr.leaveHandled(params),
    queryFn: () => leaveApi.listHandled(params),
    enabled,
  })
}

/**
 * Luồng duyệt cho cả một TRANG đơn, một lượt gọi.
 *
 * Gọi theo trang chứ không theo dòng: hai mươi dòng × một lượt gọi là hai mươi
 * lượt mạng cho một lần mở bảng. Backend cũng gom sẵn (`steps_service`), nên
 * đừng tách hook này ra thành `useFlowStrip(id)`.
 */
export function useLeaveFlowStrips(ids: number[]) {
  return useQuery({
    queryKey: queryKeys.hr.leaveFlowStrips(ids),
    queryFn: () => leaveApi.flowStrips(ids),
    enabled: ids.length > 0,
  })
}

/**
 * Duyệt · Trả về · Từ chối qua BỘ MÁY, gọi từ chính màn Nghỉ phép.
 *
 * ⚠️ Khác hẳn `useLeaveRequestAction`: cái kia bấm vào tờ ĐƠN (đường duyệt
 * thẳng, chỉ chạy khi môi trường chưa khai luồng), cái này bấm vào PHIÊN DUYỆT.
 * Gọi nhầm thì backend chặn bằng `block_legacy_path` với câu "đừng bấm duyệt
 * thẳng ở đây" — đúng luật nhưng vô nghĩa với người vừa bấm nút Duyệt.
 */
export type ApprovalDecision = 'approve' | 'return' | 'reject'

const DECISION_MESSAGES: Record<ApprovalDecision, string> = {
  approve: 'Đã duyệt đơn',
  return: 'Đã trả đơn về cho người nộp',
  reject: 'Đã từ chối đơn',
}

export function useLeaveApprovalDecision() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      instanceId,
      decision,
      reason,
    }: {
      instanceId: number
      decision: ApprovalDecision
      reason?: string
    }) => {
      if (decision === 'approve') return leaveApi.approveInstance(instanceId, reason ?? '')
      if (decision === 'reject') return leaveApi.rejectInstance(instanceId, reason ?? '')
      return leaveApi.returnInstance(instanceId, reason ?? '')
    },
    onSuccess: (_data, variables) => {
      toast.success(DECISION_MESSAGES[variables.decision])
      //  Dọn cả nhánh `hr`: một lượt ký đổi hàng đợi, đổi danh sách đơn, đổi
      //  luồng duyệt, và đổi quỹ phép của người nghỉ.
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

// ── Ngày lễ cho màn Lịch nghỉ ──────────────────────────────────────────────────

/**
 * Toàn bộ lịch ngày lễ đang bật.
 *
 * Nạp HẾT một lượt rồi lọc ở phía màn hình, không lọc theo năm ở backend: bảng
 * này cỡ vài chục dòng cho cả hệ, mà những ngày `is_recurring` thì không mang
 * năm nào cả — hỏi backend "lễ năm 2027" sẽ trượt hết Tết Dương lịch và Quốc
 * khánh vốn nhập một lần từ 2026. Luật khớp nằm ở `utils/calendar-grid.ts`.
 */
export function useHolidays() {
  return useQuery({
    queryKey: queryKeys.hr.holidays({ all: true }),
    queryFn: () => leaveApi.listHolidays({ page: 1, page_size: 500 }),
    //  Lịch lễ gần như không đổi trong một phiên làm việc.
    staleTime: 5 * 60 * 1000,
  })
}
