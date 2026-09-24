import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import {
  purchaseRequestApi,
  type PurchaseRequestPayload,
} from '../api/purchase-request-api'

/** Một phiếu YCMH. `id <= 0` (màn tạo mới) thì không gọi API. */
export function usePurchaseRequest(id: number) {
  return useQuery({
    queryKey: queryKeys.procurement.purchaseRequest(id),
    queryFn: () => purchaseRequestApi.getById(id),
    enabled: id > 0,
  })
}

/**
 * bao-CR-314 — phiếu YCMH của một ĐƠN MUA HÀNG, đã cắt còn dòng hàng của đơn đó.
 * `purchaseOrderId <= 0` (không phải chế độ in-từ-đơn) thì không gọi API.
 */
export function usePurchaseRequestOfPurchaseOrder(purchaseOrderId: number) {
  return useQuery({
    queryKey: queryKeys.procurement.purchaseRequestOfPurchaseOrder(purchaseOrderId),
    queryFn: () => purchaseRequestApi.getForPurchaseOrder(purchaseOrderId),
    enabled: purchaseOrderId > 0,
  })
}

/** Số lượng đã đặt theo mã hàng — để cột "Đã đặt" trên bảng dòng hàng. */
export function useOrderProgress(id: number) {
  return useQuery({
    queryKey: queryKeys.procurement.purchaseRequestProgress(id),
    queryFn: () => purchaseRequestApi.getOrderProgress(id),
    enabled: id > 0,
  })
}

/**
 * CR-071 — ứng viên đứng tên TBP trên phiếu, đổ vào ô "Trưởng bộ phận".
 *
 * bao-CR-474: tra theo PHÒNG BAN đang chọn trên form, giống hệt bản cũ. Bản đầu của
 * v2 tra theo id phiếu nên màn TẠO MỚI (id = 0) không có danh sách → ô về dạng chữ,
 * còn phiếu NHÂN BẢN (đã lưu nháp, có id) lại chọn được — hai màn một phiếu mà hai
 * hành vi. Tra theo phòng còn đúng hơn khi đang sửa: đổi người yêu cầu sang phòng
 * khác thì danh sách đi theo phòng mới ngay, không đợi lưu.
 */
export function useDeptHeadCandidates(department: string, companyId: number, enabled = true) {
  return useQuery({
    queryKey: [...queryKeys.procurement.purchaseRequestDeptHeads(0), 'by-department', department, companyId],
    queryFn: () => purchaseRequestApi.getDeptHeadCandidatesByDepartment(department, companyId),
    enabled: enabled && !!department,
  })
}

/**
 * bao-CR-474 — trưởng phòng MẶC ĐỊNH của phòng đang chọn, để ô TBP LUÔN hiện một người
 * khi người lập chưa chọn (`head_of_dept_id = 0`). Đó cũng là người backend tự điền lúc
 * lưu / gửi duyệt, nên màn hình và dữ liệu lưu xuống không lệch nhau.
 */
export function useDefaultDeptHead(department: string, departmentId: number, enabled = true) {
  return useQuery({
    queryKey: [...queryKeys.procurement.purchaseRequestDeptHeads(0), 'default', department, departmentId],
    queryFn: () => purchaseRequestApi.getDeptHead(department, departmentId),
    enabled: enabled && (!!department || departmentId > 0),
  })
}

/** Tạo mới HOẶC cập nhật — hai màn dùng chung một form nên gộp một hook. */
export function useSavePurchaseRequest() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, payload }: { id?: number; payload: PurchaseRequestPayload }) =>
      id ? purchaseRequestApi.update(id, payload) : purchaseRequestApi.create(payload),
    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã lưu phiếu' : 'Đã tạo phiếu')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** Tên thao tác chuyển trạng thái + câu báo thành công tương ứng. */
const ACTION_LABELS = {
  submit: 'Đã gửi duyệt',
  approve: 'Đã duyệt phiếu',
  dispatch: 'Đã điều phối',
  complete: 'Đã hoàn thành phiếu',
  reject: 'Đã trả lại phiếu',
  cancel: 'Đã từ chối phiếu',
  return: 'Đã trả phiếu về cho người yêu cầu',
  copy: 'Đã nhân bản phiếu',
} as const

export type PurchaseRequestAction = keyof typeof ACTION_LABELS

/**
 * Mọi thao tác chuyển trạng thái gom vào MỘT mutation: chúng chỉ khác nhau ở
 * đường dẫn và câu thông báo, tách tám hook chỉ tổ lặp code.
 *
 * `reason` bắt buộc với reject / cancel / return (backend cũng chặn).
 */
export function usePurchaseRequestAction(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ action, reason }: { action: PurchaseRequestAction; reason?: string }) => {
      switch (action) {
        case 'submit':
          return purchaseRequestApi.submit(id)
        case 'approve':
          return purchaseRequestApi.approve(id)
        case 'dispatch':
          return purchaseRequestApi.dispatch(id)
        case 'complete':
          return purchaseRequestApi.complete(id)
        case 'reject':
          return purchaseRequestApi.reject(id, reason ?? '')
        case 'cancel':
          return purchaseRequestApi.cancel(id, reason ?? '')
        case 'return':
          return purchaseRequestApi.returnToRequester(id, reason ?? '')
        case 'copy':
          return purchaseRequestApi.copy(id)
      }
    },
    onSuccess: (_data, variables) => {
      toast.success(ACTION_LABELS[variables.action])
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

export function useDeletePurchaseRequest() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => purchaseRequestApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa phiếu')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** Gán NSTM phụ trách cho một dòng. */
export function useAssignPurchaser(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (item: { id: number; assignee: string }) =>
      purchaseRequestApi.assign(id, [item]),
    onSuccess: () => {
      toast.success('Đã cập nhật NSTM phụ trách')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** Cập nhật tiến độ một dòng hàng. */
export function useUpdateItemStatus(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (item: {
      id: number
      line_status: string
      progress_note?: string
      note?: string
      expected_date?: string
      expected_date_reason?: string
    }) => purchaseRequestApi.updateItemStatus(id, [item]),
    onSuccess: () => {
      toast.success('Đã cập nhật tiến độ dòng')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

export function useSetUrgent(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (isUrgent: boolean) => purchaseRequestApi.setUrgent(id, isUrgent),
    onSuccess: () => {
      toast.success('Đã cập nhật Đơn gấp')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** Tham số của hộp Chuyển phòng xử lý: `handlerDeptId = 0` nghĩa là TRẢ VỀ phòng lập. */
export interface TransferDeptInput {
  handlerDeptId: number
  reason: string
}

/**
 * bao-CR-414 GĐ5 — chuyển cả phiếu YCMH sang phòng khác xử lý, hoặc trả về phòng lập.
 * Backend gỡ người phụ trách mọi dòng và ghi lý do vào nhật ký phiếu.
 */
export function useTransferPurchaseRequestDept(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ handlerDeptId, reason }: TransferDeptInput) =>
      handlerDeptId === 0
        ? purchaseRequestApi.returnDept(id, reason)
        : purchaseRequestApi.transferDept(id, handlerDeptId, reason),
    onSuccess: (_data, { handlerDeptId }) => {
      toast.success(handlerDeptId === 0 ? 'Đã trả phiếu về phòng lập' : 'Đã chuyển phòng xử lý')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}
