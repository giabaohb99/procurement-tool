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

export function useSaveApprovalNode(flowId: number) {
  const invalidate = useInvalidateApproval()

  return useMutation({
    mutationFn: ({ id, values }: { id?: number; values: Partial<ApprovalNode> }) =>
      id
        ? approvalFlowApi.updateNode(flowId, id, values)
        : approvalFlowApi.addNode(flowId, values),
    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã lưu bước' : 'Đã thêm bước')
      invalidate()
    },
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

const NHAN_THANH_CONG: Record<ApprovalActionKind, string> = {
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
 * MỘT hook cho cả năm thao tác thay vì năm hook riêng.
 *
 * Năm `useMutation` riêng thì màn hình phải theo dõi năm cờ `isPending`, và chỉ
 * cần quên một cái là người dùng bấm được nút thứ hai trong lúc nút thứ nhất
 * còn đang chạy.
 */
export function useApprovalAction(instanceId: number) {
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
      toast.success(NHAN_THANH_CONG[variables.kind])
      invalidate()
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
