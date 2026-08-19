import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { surveyRequestApi, type SurveyRequestPayload } from '../api/survey-request-api'
import { hasSurveyResult } from '../types/survey-request-detail'

/** Một phiếu YCBG. `id <= 0` (màn tạo mới) thì không gọi API. */
export function useSurveyRequest(id: number) {
  return useQuery({
    queryKey: queryKeys.procurement.surveyRequest(id),
    queryFn: () => surveyRequestApi.getById(id),
    enabled: id > 0,
  })
}

/**
 * Khung kết quả khảo sát. Chỉ gọi từ `processing` trở đi — trước đó backend chưa
 * có phương án nào để trả, hỏi sớm chỉ tổ thêm một lượt 200 rỗng mỗi lần mở phiếu.
 */
export function useSurveyRequestResult(id: number, status: string) {
  return useQuery({
    queryKey: queryKeys.procurement.surveyRequestResult(id),
    queryFn: () => surveyRequestApi.getResult(id),
    enabled: id > 0 && hasSurveyResult(status),
  })
}

/** Tạo mới HOẶC cập nhật — một form dùng cho cả hai màn. */
export function useSaveSurveyRequest() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, payload }: { id?: number; payload: SurveyRequestPayload }) =>
      id ? surveyRequestApi.update(id, payload) : surveyRequestApi.create(payload),
    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã lưu phiếu' : 'Đã tạo phiếu')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/**
 * Tra Trưởng bộ phận của một phòng, gọi ngay lúc người lập đổi phòng ban.
 *
 * Là mutation chứ không phải query: nó chạy theo THAO TÁC (đổi ô Bộ phận), không
 * phải theo dữ liệu đang hiển thị — dùng `useQuery` thì phải giữ thêm một state
 * "phòng đang tra" chỉ để kích hoạt, mà kết quả vẫn phải chép tay vào form.
 */
export function useDeptHeadLookup() {
  return useMutation({
    mutationFn: ({ department, departmentId }: { department: string; departmentId: number }) =>
      surveyRequestApi.getDeptHead(department, departmentId),
  })
}

/** Tên thao tác chuyển trạng thái + câu báo thành công tương ứng. */
const ACTION_LABELS = {
  submit: 'Đã gửi duyệt',
  approve: 'Đã duyệt phiếu',
  reject: 'Đã trả lại phiếu',
  cancel: 'Đã từ chối phiếu',
  finalize: 'Đã chuyển Hoàn thành',
  clone: 'Đã nhân bản phiếu',
} as const

export type SurveyRequestAction = keyof typeof ACTION_LABELS

/**
 * Mọi thao tác chuyển trạng thái gom vào MỘT mutation — chúng chỉ khác đường dẫn
 * và câu thông báo. `reason` bắt buộc với reject / cancel (backend cũng chặn).
 */
export function useSurveyRequestAction(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ action, reason }: { action: SurveyRequestAction; reason?: string }) => {
      switch (action) {
        case 'submit':
          return surveyRequestApi.submit(id)
        case 'approve':
          return surveyRequestApi.approve(id)
        case 'reject':
          return surveyRequestApi.reject(id, reason ?? '')
        case 'cancel':
          return surveyRequestApi.cancel(id, reason ?? '')
        case 'finalize':
          return surveyRequestApi.finalize(id)
        case 'clone':
          return surveyRequestApi.clone(id)
      }
    },
    onSuccess: (_data, variables) => {
      toast.success(ACTION_LABELS[variables.action])
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

export function useDeleteSurveyRequest() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => surveyRequestApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa phiếu')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** Gán NSTM phụ trách một dòng — chỉ phía thu mua bấm được. */
export function useAssignSurveyLine(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ lineId, assignee }: { lineId: number; assignee: string }) =>
      surveyRequestApi.setLineAssignee(id, lineId, assignee),
    onSuccess: () => {
      toast.success('Đã cập nhật NSTM phụ trách')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/**
 * Người YC chốt trạng thái một dòng (cần khảo sát lại / hoàn thành).
 * Phải nạp lại CẢ khung kết quả: "Cần khảo sát lại" bỏ chọn phương án ở backend,
 * không nạp lại thì khu Kết quả vẫn hiện phương án "Đã chọn" cũ, lệch với bảng trên.
 */
export function useSetSurveyLineStatus(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ lineId, lineStatus }: { lineId: number; lineStatus: string }) =>
      surveyRequestApi.setLineStatus(id, lineId, lineStatus),
    onSuccess: () => {
      toast.success('Đã cập nhật trạng thái dòng')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** Chọn / bỏ chọn một phương án cho một dòng. */
export function useChooseSurveyOption(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ lineId, optionId }: { lineId: number; optionId: number }) =>
      surveyRequestApi.chooseOption(id, lineId, optionId),
    onSuccess: (data, variables) => {
      const option = (data?.lines ?? [])
        .flatMap((line) => line.options ?? [])
        .find((o) => o.id === variables.optionId)
      toast.success(option?.is_chosen ? 'Đã chọn phương án' : 'Đã bỏ chọn phương án')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** Sinh YCMH từ các phương án đã chọn. */
export function useCreatePurchaseRequestsFromSurvey(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => surveyRequestApi.createPurchaseRequests(id),
    onSuccess: (data) => {
      const created = data?.created_prs ?? []
      const codes = created.map((pr) => pr.code).join(', ')
      toast.success(`Đã tạo ${created.length} phiếu yêu cầu mua: ${codes}`)
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}
