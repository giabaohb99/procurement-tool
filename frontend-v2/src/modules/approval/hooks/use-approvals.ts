import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'
import { approvalApi, approvalFlowApi, delegationApi } from '../api/approval-api'
import type { ApprovalFlow, ApprovalNode, ApprovalSwitch, Delegation } from '../types/approval'

/** Bộ máy phê duyệt dùng chung (nhóm I). */

export function useMyTasks(entity?: string) {
  return useQuery({
    queryKey: queryKeys.approval.myTasks(entity ?? ''),
    queryFn: () => approvalApi.myTasks(entity),
    //  Màn được mở nhiều nhất của cả hệ. Người khác duyệt xong thì việc biến
    //  khỏi hộp của mình — hỏi lại khi quay về tab là đủ, không cần nhịp đều.
    refetchOnWindowFocus: true,
  })
}

/**
 * «Đã duyệt gần đây» — nhìn lại phiếu chính mình vừa quyết định.
 *
 * Không tự hỏi lại theo nhịp: danh sách này chỉ dài thêm khi CHÍNH người dùng
 * bấm duyệt, mà lúc đó `useInvalidateApproval` đã nạp lại cả cụm rồi.
 */
export function useMyDecisions(entity?: string, days = 30) {
  return useQuery({
    queryKey: queryKeys.approval.myHistory(entity ?? '', days),
    queryFn: () => approvalApi.myHistory(entity, days),
  })
}

export function useApprovalOptions() {
  return useQuery({
    queryKey: queryKeys.approval.options(),
    queryFn: () => approvalFlowApi.options(),
    //  Nhãn của sáu bảng hằng số không đổi trong một phiên làm việc.
    staleTime: Infinity,
  })
}

export function useApprovalFlows(entity?: string) {
  return useQuery({
    queryKey: queryKeys.approval.flows(entity ?? ''),
    queryFn: () => approvalFlowApi.list(entity),
  })
}

export function useApprovalFlow(id?: number) {
  return useQuery({
    queryKey: queryKeys.approval.flow(id ?? 0),
    queryFn: () => approvalFlowApi.getById(id as number),
    enabled: typeof id === 'number' && id > 0,
  })
}

export function useApprovalTrail(instanceId?: number) {
  return useQuery({
    queryKey: queryKeys.approval.trail(instanceId ?? 0),
    queryFn: () => approvalApi.trail(instanceId as number),
    enabled: typeof instanceId === 'number' && instanceId > 0,
  })
}

/**
 * Phiên duyệt của MỘT chứng từ, cho trang chi tiết của chứng từ đó.
 *
 * Trả `null` khi chứng từ chưa từng vào bộ máy — đó là câu trả lời hợp lệ, không
 * phải lỗi, và là cách trang chi tiết biết mình còn đang chạy luồng một bước cũ.
 */
export function useEntityApproval(entity: string, entityId?: number) {
  return useQuery({
    queryKey: queryKeys.approval.ofEntity(entity, entityId ?? 0),
    queryFn: () => approvalApi.ofEntity(entity, entityId as number),
    enabled: typeof entityId === 'number' && entityId > 0,
  })
}

export function useApprovalSwitches() {
  return useQuery({
    queryKey: queryKeys.approval.switches(),
    queryFn: () => approvalFlowApi.switches(),
  })
}

function useInvalidateApproval() {
  const queryClient = useQueryClient()
  return () => void queryClient.invalidateQueries({ queryKey: queryKeys.approval.all })
}

export function useSaveApprovalFlow() {
  const invalidate = useInvalidateApproval()

  return useMutation({
    mutationFn: ({ id, values }: { id?: number; values: Partial<ApprovalFlow> }) =>
      id ? approvalFlowApi.update(id, values) : approvalFlowApi.create(values),
    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã lưu luồng duyệt' : 'Đã tạo luồng duyệt')
      invalidate()
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}

export function useDeleteApprovalFlow() {
  const invalidate = useInvalidateApproval()

  return useMutation({
    mutationFn: (id: number) => approvalFlowApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa luồng duyệt')
      invalidate()
    },
    //  Backend CHẶN xóa khi còn phiếu đang chạy theo luồng
    //  (`_chan_khi_dang_chay`) và câu chặn đó đã nói rõ nên làm gì thay thế —
    //  hiện nguyên văn, đừng thay bằng câu chung chung "Xóa thất bại".
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}

export function useSaveApprovalNode(flowId: number) {
  const invalidate = useInvalidateApproval()

  return useMutation({
    mutationFn: ({
      id,
      values,
      asBranch,
    }: {
      id?: number
      values: Partial<ApprovalNode>
      /** Chỉ dùng khi THÊM: bước mới là nhánh song song của chặng đó. */
      asBranch?: boolean
    }) =>
      id
        ? approvalFlowApi.updateNode(flowId, id, values)
        : approvalFlowApi.addNode(flowId, values, asBranch),
    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã lưu bước' : 'Đã thêm bước')
      invalidate()
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}

export function useReorderApprovalNodes(flowId: number) {
  const invalidate = useInvalidateApproval()

  return useMutation({
    mutationFn: (stages: number[][]) => approvalFlowApi.reorderNodes(flowId, stages),
    onSuccess: invalidate,
    //  Không toast khi thành công: kéo thả đã tự nói ra kết quả trên màn hình,
    //  thêm một dòng thông báo mỗi lần kéo chỉ tổ che mất sơ đồ.
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}

export function useDeleteApprovalNode(flowId: number) {
  const invalidate = useInvalidateApproval()

  return useMutation({
    mutationFn: (nodeId: number) => approvalFlowApi.removeNode(flowId, nodeId),
    onSuccess: () => {
      toast.success('Đã xóa bước')
      invalidate()
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}

export function useSetApprovalSwitch() {
  const invalidate = useInvalidateApproval()

  return useMutation({
    mutationFn: (values: ApprovalSwitch) => approvalFlowApi.setSwitch(values),
    onSuccess: (_data, variables) => {
      toast.success(
        variables.is_enabled
          ? 'Đã bật bộ máy duyệt mới — phiếu tạo từ giờ chạy theo luồng đã khai'
          : 'Đã tắt — chứng từ loại này quay về đường duyệt cũ',
      )
      invalidate()
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}

/** Năm thao tác trên phiếu — xem `action_service.py`. */
export type ApprovalActionKind = 'approve' | 'reject' | 'return' | 'withdraw' | 'comment'

const SUCCESS_LABELS: Record<ApprovalActionKind, string> = {
  approve: 'Đã duyệt',
  reject: 'Đã từ chối',
  return: 'Đã trả lại',
  withdraw: 'Đã rút lại',
  comment: 'Đã ghi ý kiến',
}

interface ApprovalActionInput {
  kind: ApprovalActionKind
  /** Ý kiến khi duyệt, hoặc LÝ DO khi từ chối / trả lại / rút — backend bắt buộc. */
  text: string
  /** Trả về đúng một bước phía trước; bỏ trống là trả về người nộp. */
  toSeq?: number | null
}

/**
 * Họ query của CHÍNH CHỨNG TỪ, theo `entity` của phiếu duyệt.
 *
 * Một cú bấm duyệt / trả lại / từ chối đổi trạng thái của chứng từ chứ không chỉ
 * của phiên duyệt, nên nạp lại mỗi cụm `approval` là chưa đủ.
 *
 * ⚠️ LỖI ĐÃ XẢY RA (24/08/2026): trả lại một văn bản ngay trên trang chi tiết thì
 * băng đổi thành «Văn bản bị trả về» nhưng nhãn trạng thái ở đầu trang vẫn ghi
 * «Đang duyệt», nội dung vẫn khóa, nút *Gửi duyệt* vẫn chưa hiện — tới khi người
 * dùng tự F5. Một trang tự mâu thuẫn với chính nó, và người đọc thì kết luận là
 * bấm chưa ăn. Cùng đúng loại lỗi đã vá ở `use-documents.ts::refresh`, chỉ là ở
 * đầu bên kia.
 */
const HO_QUERY_CUA_CHUNG_TU: Record<string, readonly string[]> = {
  document: queryKeys.document.all,
  purchase_request: queryKeys.procurement.all,
  survey_request: queryKeys.procurement.all,
  purchase_order: queryKeys.procurement.all,
  //  Nghỉ phép và Đặt phòng nằm trong phân hệ Nhân sự — ký xong phải nạp lại cả
  //  họ `hr`, vì một phiếu xuất hiện ở danh sách, ở chi tiết và ở lịch.
  leave_request: queryKeys.hr.all,
  room_booking: queryKeys.hr.all,
}

/**
 * MỘT hook cho cả năm thao tác thay vì năm hook riêng.
 *
 * Năm `useMutation` riêng thì màn hình phải theo dõi năm cờ `isPending`, và chỉ
 * cần quên một cái là người dùng bấm được nút thứ hai trong lúc nút thứ nhất
 * còn đang chạy.
 *
 * `entity` là loại chứng từ của phiếu (`task.entity`) — để nạp lại luôn dữ liệu
 * chứng từ, xem `HO_QUERY_CUA_CHUNG_TU`. Bỏ trống thì chỉ nạp lại cụm duyệt, và
 * màn chi tiết chứng từ sẽ hiện số liệu cũ cho tới lần F5 kế tiếp.
 */
export function useApprovalAction(instanceId: number, entity?: string) {
  const queryClient = useQueryClient()
  const invalidate = useInvalidateApproval()

  return useMutation({
    mutationFn: ({ kind, text, toSeq }: ApprovalActionInput) => {
      if (kind === 'approve') return approvalApi.approve(instanceId, text)
      if (kind === 'reject') return approvalApi.reject(instanceId, text)
      if (kind === 'return') return approvalApi.return(instanceId, text, toSeq)
      if (kind === 'withdraw') return approvalApi.withdraw(instanceId, text)
      return approvalApi.comment(instanceId, text)
    },
    onSuccess: (_data, variables) => {
      toast.success(SUCCESS_LABELS[variables.kind])
      invalidate()
      //  «Ghi ý kiến» KHÔNG đổi trạng thái chứng từ (xem `action_service.gop_y`)
      //  nên không cần kéo cả họ query của nó về lại.
      const ho = variables.kind !== 'comment' && entity ? HO_QUERY_CUA_CHUNG_TU[entity] : undefined
      if (ho) void queryClient.invalidateQueries({ queryKey: ho })
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}

export function useDelegations(employeeId?: number) {
  return useQuery({
    queryKey: queryKeys.approval.delegations(employeeId ?? 0),
    queryFn: () => delegationApi.list(employeeId),
  })
}

export function useSaveDelegation() {
  const invalidate = useInvalidateApproval()

  return useMutation({
    mutationFn: ({ id, values }: { id?: number; values: Partial<Delegation> }) =>
      id ? delegationApi.update(id, values) : delegationApi.create(values),
    onSuccess: () => {
      toast.success('Đã lưu ủy quyền')
      invalidate()
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}

export function useStopDelegation() {
  const invalidate = useInvalidateApproval()

  return useMutation({
    mutationFn: (id: number) => delegationApi.stop(id),
    onSuccess: () => {
      toast.success('Đã ngưng ủy quyền')
      invalidate()
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}
