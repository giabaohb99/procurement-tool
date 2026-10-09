import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { executionReportApi, type ReportDocPayload } from '../api/survey-request-report-api'
import {
  REPORT_DOC_STATUS_LABELS,
  type ReportFirstDocPayload,
  type ReportOwnerEntity,
  type SurveyRequestReport,
} from '../types/survey-request-report'

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
 * Ô chọn dòng hàng + giai đoạn của hộp «Thêm hồ sơ» khi khối còn trống (duoc-CR-611).
 * Chỉ gọi khi hộp MỞ — khối đã có nội dung thì không ai cần tới nó.
 */
export function useReportFirstDocOptions(
  id: number,
  entity: ReportOwnerEntity,
  enabled: boolean,
) {
  return useQuery({
    queryKey: queryKeys.procurement.executionReportFirstDocOptions(entity, id),
    queryFn: () => executionReportApi(entity).firstDocOptions(id),
    enabled: enabled && id > 0,
  })
}

/**
 * Khóa của MỌI mutation trên một khối báo cáo — vừa làm khóa xếp hàng (`scope`) vừa để
 * đếm số lượt đang chờ. Chỉ hook này dùng, không ai invalidate theo nó nên để tại chỗ
 * thay vì đưa vào `query-keys.ts` (đúng ngoại lệ ghi ở `naming.md`).
 */
const reportMutationKey = (entity: ReportOwnerEntity, id: number) =>
  ['execution-report-mutation', entity, id] as const

/** Trộn `changes` vào đúng hồ sơ trong cache — để ô vừa sửa đổi NGAY, không chờ máy chủ. */
type ReportOptimisticPatch<TVars> = (
  report: SurveyRequestReport,
  vars: TVars,
) => SurveyRequestReport

/**
 * Ô chọn mẫu của hộp «Khởi tạo báo cáo mẫu» (duoc-CR-614). Chỉ gọi khi hộp MỞ, và
 * danh sách mẫu nằm trong mã nguồn backend nên giữ lâu không cần tải lại.
 */
export function useReportTemplates(id: number, entity: ReportOwnerEntity, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.procurement.executionReportTemplates(entity, id),
    queryFn: () => executionReportApi(entity).templates(id),
    enabled: enabled && id > 0,
    staleTime: Infinity,
  })
}

/**
 * Mọi mutation của khối báo cáo trả về NGUYÊN khối mới → ghi thẳng vào cache
 * thay vì invalidate: đỡ một lượt GET, và màn hình đổi ngay khi bấm ✓.
 *
 * duoc-CR-612 — dạng «Bảng» bắn PATCH liên tục (mỗi ô một lượt), nên:
 * - Mọi lượt của CÙNG khối chạy LẦN LƯỢT (`scope`): ✓, sửa ô, hộp sửa, xóa… về sai thứ
 *   tự thì bản cũ đè bản mới (ô vừa sửa nhảy về giá trị cũ, ✓ đảo sai chiều).
 * - Còn lượt khác đang chờ phía sau thì KHÔNG ghi cache: lượt sau trả khối mới hơn, ghi
 *   bản này là xóa mất giá trị tạm của lượt sau trong một khoảnh khắc.
 * - `optimistic` (tùy chọn) sửa cache ngay khi bấm; hỏng thì trả lại ảnh cũ và tải lại
 *   khối từ máy chủ cho chắc.
 */
function useReportMutation<TVars>(
  entity: ReportOwnerEntity,
  id: number,
  mutationFn: (vars: TVars) => Promise<SurveyRequestReport>,
  successMessage?: string,
  optimistic?: ReportOptimisticPatch<TVars>,
) {
  const queryClient = useQueryClient()
  const reportKey = queryKeys.procurement.executionReport(entity, id)
  const mutationKey = reportMutationKey(entity, id)
  return useMutation({
    mutationKey,
    mutationFn,
    scope: { id: mutationKey.join(':') },
    onMutate: async (vars: TVars) => {
      if (!optimistic) return { previous: undefined }
      await queryClient.cancelQueries({ queryKey: reportKey })
      const previous = queryClient.getQueryData<SurveyRequestReport>(reportKey)
      if (previous) queryClient.setQueryData(reportKey, optimistic(previous, vars))
      return { previous }
    },
    onError: (_error, _vars, context) => {
      if (context?.previous) queryClient.setQueryData(reportKey, context.previous)
      void queryClient.invalidateQueries({ queryKey: reportKey })
    },
    onSuccess: (data) => {
      if (successMessage) toast.success(successMessage)
      //  Lượt đang chạy cũng còn tính là «đang chờ» lúc này nên mốc là 1.
      if (queryClient.isMutating({ mutationKey }) <= 1) queryClient.setQueryData(reportKey, data)
      //  Mọi thao tác báo cáo đều ghi Lịch sử thao tác của chứng từ cha — làm mới
      //  nó để dòng mới hiện ngay (nhất là dòng «Xóa» có nút Hoàn tác).
      void queryClient.invalidateQueries({ queryKey: ['audit-logs', entity, id] })
    },
  })
}

/** Áp `changes` vào một hồ sơ trong khối — nhãn trạng thái đi theo mã cho pill đổi chữ luôn. */
function mergeDocChanges(
  report: SurveyRequestReport,
  docId: number,
  changes: Partial<ReportDocPayload>,
): SurveyRequestReport {
  return {
    ...report,
    docs: report.docs.map((doc) =>
      doc.id === docId
        ? {
            ...doc,
            ...changes,
            status_label:
              changes.status === undefined
                ? doc.status_label
                : (REPORT_DOC_STATUS_LABELS[changes.status] ?? doc.status_label),
          }
        : doc,
    ),
  }
}

/** Thêm mới (`docId` bỏ trống, đủ trường) hoặc sửa (chỉ gửi trường đổi) một hồ sơ. */
export type SaveReportDocVars =
  | { docId: number; payload: Partial<ReportDocPayload> }
  | { docId?: undefined; payload: ReportDocPayload }

/** Toàn bộ thao tác ghi của khối báo cáo — backend gác theo cửa ghi của chứng từ cha. */
export function useSurveyReportActions(id: number, entity: ReportOwnerEntity = 'survey_request') {
  const api = executionReportApi(entity)
  return {
    init: useReportMutation(
      entity,
      id,
      (template: number) => api.init(id, template),
      'Đã khởi tạo báo cáo theo mẫu đã chọn',
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
      (vars: SaveReportDocVars) =>
        vars.docId === undefined
          ? api.createDoc(id, vars.payload)
          : api.updateDoc(id, vars.docId, vars.payload),
      'Đã lưu hồ sơ',
    ),
    /** Nút ✓ — chỉ đổi trạng thái, không toast để bấm liên tiếp không dội thông báo. */
    setDocStatus: useReportMutation(
      entity,
      id,
      ({ docId, status }: { docId: number; status: number }) =>
        api.updateDoc(id, docId, { status }),
      undefined,
      (report, { docId, status }) => mergeDocChanges(report, docId, { status }),
    ),
    /**
     * Sửa MỘT ô ngay trên dòng của dạng «Bảng» (duoc-CR-612): chỉ gửi trường vừa đổi,
     * không toast — mỗi ô một lần lưu, báo thành công từng ô thì dội thông báo.
     * Lỗi vẫn hiện qua lớp báo lỗi chung của `@/core/api`.
     */
    patchDoc: useReportMutation(
      entity,
      id,
      ({ docId, changes }: { docId: number; changes: Partial<ReportDocPayload> }) =>
        api.updateDoc(id, docId, changes),
      undefined,
      (report, { docId, changes }) => mergeDocChanges(report, docId, changes),
    ),
    deleteDoc: useReportMutation(
      entity,
      id,
      ({ docId }: { docId: number }) => api.deleteDoc(id, docId),
      'Đã xóa hồ sơ',
    ),
    /** Hồ sơ ĐẦU TIÊN khi khối còn trống — backend dựng khung rồi thêm đúng hồ sơ đó. */
    createFirstDoc: useReportMutation(
      entity,
      id,
      (payload: ReportFirstDocPayload) => api.createFirstDoc(id, payload),
      'Đã thêm hồ sơ đầu tiên',
    ),
    /** Xóa nhiều hồ sơ (chọn tay / cả cụm một dòng hàng) — câu báo có số lượng, chỗ gọi lo. */
    deleteDocs: useReportMutation(
      entity,
      id,
      ({ docIds }: { docIds: number[] }) => api.deleteDocs(id, docIds),
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
