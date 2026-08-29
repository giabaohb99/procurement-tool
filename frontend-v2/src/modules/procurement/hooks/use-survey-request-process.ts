import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { surveyRequestApi } from '../api/survey-request-api'
import type { AvailableSurveyLinesParams } from '../types/survey-request-process'

/**
 * Khung XỬ LÝ KHẢO SÁT của một YCBG — chỉ bật khi người xem có quyền `process`
 * và phiếu đã sang trạng thái xử lý được (caller quyết qua `enabled`).
 *
 * `retry: false` là CỐ Ý: Admin hệ thống có quyền `survey_request.process` nhưng
 * KHÔNG phải nhân sự thu mua sẽ ăn 403 từ gác `_purchaser` — thử lại chỉ tổ
 * bắn thêm ba lượt 403 rồi vẫn thất bại; card tự ẩn khi query lỗi.
 */
export function useSurveyRequestProcess(id: number, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.procurement.surveyRequestProcess(id),
    queryFn: () => surveyRequestApi.getProcess(id),
    enabled: id > 0 && enabled,
    retry: false,
  })
}

/**
 * Bảng "Kết quả khảo sát đã duyệt" chọn được cho MỘT dòng. Backend đòi ít nhất
 * một tiêu chí lọc; thiếu thì đừng gọi (`enabled` phía caller) — gọi cũng chỉ
 * nhận về danh sách rỗng.
 */
export function useAvailableSurveyLines(
  id: number,
  lineId: number,
  params: AvailableSurveyLinesParams,
  enabled: boolean,
) {
  return useQuery({
    queryKey: queryKeys.procurement.surveyRequestAvailableLines(id, lineId, { ...params }),
    queryFn: () => surveyRequestApi.listAvailableSurveyLines(id, lineId, params),
    enabled: id > 0 && lineId > 0 && enabled,
    // Giữ trang cũ trên màn trong lúc tải trang mới — bảng không giật về rỗng.
    placeholderData: keepPreviousData,
  })
}

/** Gắn một dòng khảo sát đã duyệt làm phương án cho một dòng YCBG. */
export function useAddProcessOption(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      lineId,
      productSurveyLineId,
    }: {
      lineId: number
      productSurveyLineId: number
    }) => surveyRequestApi.addProcessOption(id, lineId, productSurveyLineId),
    onSuccess: () => {
      toast.success('Đã thêm phương án')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

export function useRemoveProcessOption(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ lineId, optionId }: { lineId: number; optionId: number }) =>
      surveyRequestApi.removeProcessOption(id, lineId, optionId),
    onSuccess: () => {
      toast.success('Đã xóa phương án')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** Sửa Mã SP hệ thống / ghi chú NSTM của một phương án đã gắn. */
export function useUpdateProcessOption(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      lineId,
      optionId,
      payload,
    }: {
      lineId: number
      optionId: number
      payload: { system_product_code?: string; nstm_note?: string }
    }) => surveyRequestApi.updateProcessOption(id, lineId, optionId, payload),
    onSuccess: () => {
      toast.success('Đã cập nhật phương án')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** Lấy phương án tự động từ các Phiếu khảo sát đã duyệt liên kết với YCBG. */
export function useSyncProcessOptions(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => surveyRequestApi.syncProcessOptions(id),
    onSuccess: () => {
      toast.success('Đã lấy phương án mới từ khảo sát')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** NSTM chốt hoàn thành phần khảo sát của mình (kèm các dòng chốt RỖNG). */
export function useCompleteProcess(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (emptyLineIds: number[]) => surveyRequestApi.completeProcess(id, emptyLineIds),
    onSuccess: () => {
      toast.success('Đã chốt phần khảo sát của bạn')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}
