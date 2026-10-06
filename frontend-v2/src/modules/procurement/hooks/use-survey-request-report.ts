import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { executionReportApi, type ReportDocPayload } from '../api/survey-request-report-api'
import type { ReportOwnerEntity, SurveyRequestReport } from '../types/survey-request-report'

/**
 * Khối báo cáo thực hiện của một chứng từ — YCBG hay ĐMH tùy `entity`
 * (bao-CR-602). `id <= 0` (màn tạo mới) không gọi.
 */
export function useSurveyRequestReport(id: number, entity: ReportOwnerEntity = 'survey_request') {
  return useQuery({
    queryKey: queryKeys.procurement.executionReport(entity, id),
    queryFn: () => executionReportApi(entity).get(id),
    enabled: id > 0,
  })
}

/**
 * Mọi mutation của khối báo cáo trả về NGUYÊN khối mới → ghi thẳng vào cache
 * thay vì invalidate: đỡ một lượt GET, và màn hình đổi ngay khi bấm ✓.
 */
function useReportMutation<TVars>(
  entity: ReportOwnerEntity,
  id: number,
  mutationFn: (vars: TVars) => Promise<SurveyRequestReport>,
  successMessage?: string,
) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn,
    onSuccess: (data) => {
      if (successMessage) toast.success(successMessage)
      queryClient.setQueryData(queryKeys.procurement.executionReport(entity, id), data)
      //  Mọi thao tác báo cáo đều ghi Lịch sử thao tác của chứng từ cha — làm mới
      //  nó để dòng mới hiện ngay (nhất là dòng «Xóa» có nút Hoàn tác).
      void queryClient.invalidateQueries({ queryKey: ['audit-logs', entity, id] })
    },
  })
}

/** Toàn bộ thao tác ghi của khối báo cáo — backend gác theo cửa ghi của chứng từ cha. */
export function useSurveyReportActions(id: number, entity: ReportOwnerEntity = 'survey_request') {
  const api = executionReportApi(entity)
  return {
    init: useReportMutation<void>(
      entity,
      id,
      () => api.init(id),
      'Đã khởi tạo báo cáo theo mẫu chung',
    ),
    /**
     * «Tạo mẫu» vào một nút / một giai đoạn. Không toast ở đây: có thêm mấy hồ
     * sơ (hay không thêm gì vì đã đủ) chỉ biết khi so khối trước/sau — chỗ gọi lo.
     */
    applyTemplate: useReportMutation(
      entity,
      id,
      ({ itemId, phaseId }: { itemId: number; phaseId?: number }) =>
        api.applyTemplate(id, itemId, phaseId),
    ),

    saveItem: useReportMutation(
      entity,
      id,
      ({ itemId, name }: { itemId?: number; name: string }) =>
        itemId ? api.renameItem(id, itemId, name) : api.createItem(id, name),
      'Đã lưu nút dòng hàng',
    ),
    deleteItem: useReportMutation(
      entity,
      id,
      ({ itemId }: { itemId: number }) => api.deleteItem(id, itemId),
      'Đã xóa nút — hồ sơ gắn nút chuyển về Chung',
    ),

    savePhase: useReportMutation(
      entity,
      id,
      ({ phaseId, name, location }: { phaseId?: number; name: string; location: string }) =>
        phaseId ? api.updatePhase(id, phaseId, name, location) : api.createPhase(id, name, location),
      'Đã lưu giai đoạn',
    ),
    deletePhase: useReportMutation(
      entity,
      id,
      ({ phaseId }: { phaseId: number }) => api.deletePhase(id, phaseId),
      'Đã xóa giai đoạn',
    ),

    saveDoc: useReportMutation(
      entity,
      id,
      ({ docId, payload }: { docId?: number; payload: ReportDocPayload }) =>
        docId ? api.updateDoc(id, docId, payload) : api.createDoc(id, payload),
      'Đã lưu hồ sơ',
    ),
    /** Nút ✓ — chỉ đổi trạng thái, không toast để bấm liên tiếp không dội thông báo. */
    setDocStatus: useReportMutation(
      entity,
      id,
      ({ docId, status }: { docId: number; status: number }) =>
        api.updateDoc(id, docId, { status }),
    ),
    deleteDoc: useReportMutation(
      entity,
      id,
      ({ docId }: { docId: number }) => api.deleteDoc(id, docId),
      'Đã xóa hồ sơ',
    ),

    /** Xóa CẢ khối — hoàn tác được từ Lịch sử thao tác. */
    deleteReport: useReportMutation<void>(
      entity,
      id,
      () => api.deleteAll(id),
      'Đã xóa báo cáo thực hiện — có thể hoàn tác ở Lịch sử thao tác',
    ),
    restoreReport: useReportMutation<void>(
      entity,
      id,
      () => api.restore(id),
      'Đã hoàn tác — khôi phục báo cáo thực hiện',
    ),
  }
}

export type SurveyReportActions = ReturnType<typeof useSurveyReportActions>

/** Hoàn tác lần «Xóa báo cáo thực hiện» — dùng ở nút trên Lịch sử thao tác. */
export function useRestoreSurveyReport(id: number, entity: ReportOwnerEntity = 'survey_request') {
  return useReportMutation<void>(
    entity,
    id,
    () => executionReportApi(entity).restore(id),
    'Đã hoàn tác — khôi phục báo cáo thực hiện',
  )
}
