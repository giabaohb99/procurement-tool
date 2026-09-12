import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import {
  surveyRequestReportApi,
  type ReportDocPayload,
} from '../api/survey-request-report-api'
import type { SurveyRequestReport } from '../types/survey-request-report'

/** Khối báo cáo thực hiện của một phiếu YCBG. `id <= 0` (màn tạo mới) không gọi. */
export function useSurveyRequestReport(id: number) {
  return useQuery({
    queryKey: queryKeys.procurement.surveyRequestReport(id),
    queryFn: () => surveyRequestReportApi.get(id),
    enabled: id > 0,
  })
}

/**
 * Mọi mutation của khối báo cáo trả về NGUYÊN khối mới → ghi thẳng vào cache
 * thay vì invalidate: đỡ một lượt GET, và màn hình đổi ngay khi bấm ✓.
 */
function useReportMutation<TVars>(
  id: number,
  mutationFn: (vars: TVars) => Promise<SurveyRequestReport>,
  successMessage?: string,
) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn,
    onSuccess: (data) => {
      if (successMessage) toast.success(successMessage)
      queryClient.setQueryData(queryKeys.procurement.surveyRequestReport(id), data)
      //  Mọi thao tác báo cáo đều ghi Lịch sử thao tác của phiếu — làm mới nó để
      //  dòng mới hiện ngay (nhất là dòng «Xóa» có nút Hoàn tác).
      void queryClient.invalidateQueries({ queryKey: ['audit-logs', 'survey_request', id] })
    },
  })
}

/** Toàn bộ thao tác ghi của khối báo cáo — chỉ NS Thu mua (cờ `process`) gọi được. */
export function useSurveyReportActions(id: number) {
  return {
    init: useReportMutation<void>(
      id,
      () => surveyRequestReportApi.init(id),
      'Đã khởi tạo báo cáo theo mẫu chung',
    ),
    /**
     * «Tạo mẫu» vào một nút / một giai đoạn. Không toast ở đây: có thêm mấy hồ
     * sơ (hay không thêm gì vì đã đủ) chỉ biết khi so khối trước/sau — chỗ gọi lo.
     */
    applyTemplate: useReportMutation(
      id,
      ({ itemId, phaseId }: { itemId: number; phaseId?: number }) =>
        surveyRequestReportApi.applyTemplate(id, itemId, phaseId),
    ),

    saveItem: useReportMutation(
      id,
      ({ itemId, name }: { itemId?: number; name: string }) =>
        itemId
          ? surveyRequestReportApi.renameItem(id, itemId, name)
          : surveyRequestReportApi.createItem(id, name),
      'Đã lưu nút dòng hàng',
    ),
    deleteItem: useReportMutation(
      id,
      ({ itemId }: { itemId: number }) => surveyRequestReportApi.deleteItem(id, itemId),
      'Đã xóa nút — hồ sơ gắn nút chuyển về Chung',
    ),

    savePhase: useReportMutation(
      id,
      ({ phaseId, name, location }: { phaseId?: number; name: string; location: string }) =>
        phaseId
          ? surveyRequestReportApi.updatePhase(id, phaseId, name, location)
          : surveyRequestReportApi.createPhase(id, name, location),
      'Đã lưu giai đoạn',
    ),
    deletePhase: useReportMutation(
      id,
      ({ phaseId }: { phaseId: number }) => surveyRequestReportApi.deletePhase(id, phaseId),
      'Đã xóa giai đoạn',
    ),

    saveDoc: useReportMutation(
      id,
      ({ docId, payload }: { docId?: number; payload: ReportDocPayload }) =>
        docId
          ? surveyRequestReportApi.updateDoc(id, docId, payload)
          : surveyRequestReportApi.createDoc(id, payload),
      'Đã lưu hồ sơ',
    ),
    /** Nút ✓ — chỉ đổi trạng thái, không toast để bấm liên tiếp không dội thông báo. */
    setDocStatus: useReportMutation(
      id,
      ({ docId, status }: { docId: number; status: number }) =>
        surveyRequestReportApi.updateDoc(id, docId, { status }),
    ),
    deleteDoc: useReportMutation(
      id,
      ({ docId }: { docId: number }) => surveyRequestReportApi.deleteDoc(id, docId),
      'Đã xóa hồ sơ',
    ),

    /** Xóa CẢ khối — hoàn tác được từ Lịch sử thao tác. */
    deleteReport: useReportMutation<void>(
      id,
      () => surveyRequestReportApi.deleteAll(id),
      'Đã xóa báo cáo thực hiện — có thể hoàn tác ở Lịch sử thao tác',
    ),
    restoreReport: useReportMutation<void>(
      id,
      () => surveyRequestReportApi.restore(id),
      'Đã hoàn tác — khôi phục báo cáo thực hiện',
    ),
  }
}

export type SurveyReportActions = ReturnType<typeof useSurveyReportActions>

/** Hoàn tác lần «Xóa báo cáo thực hiện» — dùng ở nút trên Lịch sử thao tác. */
export function useRestoreSurveyReport(id: number) {
  return useReportMutation<void>(
    id,
    () => surveyRequestReportApi.restore(id),
    'Đã hoàn tác — khôi phục báo cáo thực hiện',
  )
}
