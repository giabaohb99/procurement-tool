import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { ReportOwnerEntity, SurveyRequestReport } from '../types/survey-request-report'

/** Payload thêm/sửa một hồ sơ trong khối báo cáo. */
export interface ReportDocPayload {
  title: string
  description: string
  phase_id: number
  item_id: number
  required: boolean
  status: number
  file_note: string
  /** Kết quả / ghi chú sau khi làm (bao-CR-598). */
  result: string
  depends: number[]
  /** `yyyy-mm-dd` | `''`. */
  start_date: string
  /** `yyyy-mm-dd` | `''`. */
  expires_at: string
  /** Dự định hoàn tất — `yyyy-mm-dd` | `''`. */
  planned_date: string
  /** Id `tab_employee`, `0` = chưa cử. */
  assignee_id: number
}

/**
 * Một bộ đường API cho MỌI chứng từ chủ (bao-CR-598): `entity` chọn luật ở
 * backend — YCBG (`survey_request`) hay ĐMH (`purchase_order`).
 */
const base = (entity: ReportOwnerEntity, id: number) => `/api/execution-report/${entity}/${id}`

/**
 * Tầng API khối Báo cáo thực hiện. Mọi mutation trả về NGUYÊN khối báo cáo mới —
 * hook thay thẳng cache, không vá tay từng mảnh.
 */
export function executionReportApi(entity: ReportOwnerEntity) {
  return {
    get: (id: number) => apiGet<SurveyRequestReport>(base(entity, id)),

    /** Khởi tạo theo mẫu chung: 5 giai đoạn + hồ sơ chung của mẫu + nút theo dòng hàng. Idempotent. */
    init: (id: number) => apiPost<SurveyRequestReport>(`${base(entity, id)}/init`, {}),
    /**
     * «Tạo mẫu»: đổ mẫu chung vào một nút dòng hàng (`0` = Chung), hoặc chỉ vào
     * một giai đoạn. CỘNG THÊM — hồ sơ trùng tiêu đề đã có thì bỏ qua, nên bấm hai
     * lần không nhân đôi; số hồ sơ không đổi nghĩa là mẫu đã có đủ ở đó.
     */
    applyTemplate: (id: number, itemId: number, phaseId?: number) =>
      apiPost<SurveyRequestReport>(`${base(entity, id)}/apply-template`, {
        item_id: itemId,
        phase_id: phaseId ?? null,
      }),

    /** Xóa CẢ khối báo cáo — có thể hoàn tác từ Lịch sử thao tác. */
    deleteAll: (id: number) => apiDelete<SurveyRequestReport>(base(entity, id)),
    /** Hoàn tác lần xóa gần nhất — dựng lại khối từ ảnh chụp. */
    restore: (id: number) => apiPost<SurveyRequestReport>(`${base(entity, id)}/restore`, {}),

    createItem: (id: number, name: string) =>
      apiPost<SurveyRequestReport>(`${base(entity, id)}/items`, { name }),
    renameItem: (id: number, itemId: number, name: string) =>
      apiPatch<SurveyRequestReport>(`${base(entity, id)}/items/${itemId}`, { name }),
    /** Xóa nút — hồ sơ đang gắn nút chuyển về «Chung», không bị xóa lây. */
    deleteItem: (id: number, itemId: number) =>
      apiDelete<SurveyRequestReport>(`${base(entity, id)}/items/${itemId}`),

    createPhase: (id: number, name: string, location: string) =>
      apiPost<SurveyRequestReport>(`${base(entity, id)}/phases`, { name, location }),
    updatePhase: (id: number, phaseId: number, name: string, location: string) =>
      apiPatch<SurveyRequestReport>(`${base(entity, id)}/phases/${phaseId}`, { name, location }),
    /** Backend CHẶN xóa giai đoạn còn hồ sơ — chuyển hồ sơ đi trước. */
    deletePhase: (id: number, phaseId: number) =>
      apiDelete<SurveyRequestReport>(`${base(entity, id)}/phases/${phaseId}`),

    createDoc: (id: number, payload: ReportDocPayload) =>
      apiPost<SurveyRequestReport>(`${base(entity, id)}/docs`, payload),
    /** Gửi trường nào đổi trường đó — nút ✓ chỉ gửi mỗi `status`. */
    updateDoc: (id: number, docId: number, payload: Partial<ReportDocPayload>) =>
      apiPatch<SurveyRequestReport>(`${base(entity, id)}/docs/${docId}`, payload),
    deleteDoc: (id: number, docId: number) =>
      apiDelete<SurveyRequestReport>(`${base(entity, id)}/docs/${docId}`),
  }
}

/** Bản cũ cho YCBG — giữ tên để chỗ gọi cũ không đổi. */
export const surveyRequestReportApi = executionReportApi('survey_request')
