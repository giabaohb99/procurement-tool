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
    },
  })
}

/** Toàn bộ thao tác ghi của khối báo cáo — chỉ NS Thu mua (cờ `process`) gọi được. */
export function useSurveyReportActions(id: number) {
  return {
    init: useReportMutation<void>(id, () => surveyRequestReportApi.init(id), 'Đã khởi tạo báo cáo'),

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
  }
}

export type SurveyReportActions = ReturnType<typeof useSurveyReportActions>
