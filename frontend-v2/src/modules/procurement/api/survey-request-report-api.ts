import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { SurveyRequestReport } from '../types/survey-request-report'

/** Payload thêm/sửa một hồ sơ trong khối báo cáo. */
export interface ReportDocPayload {
  title: string
  description: string
  phase_id: number
  item_id: number
  required: boolean
  status: number
  file_note: string
  depends: number[]
  /** `yyyy-mm-dd` | `''`. */
  start_date: string
  /** `yyyy-mm-dd` | `''`. */
  expires_at: string
  /** Id `tab_employee`, `0` = chưa cử. */
  assignee_id: number
}

const base = (id: number) => `/api/survey-requests/${id}/report`

/**
 * Tầng API khối Báo cáo thực hiện của YCBG. Mọi mutation trả về NGUYÊN khối
 * báo cáo mới — hook thay thẳng cache, không vá tay từng mảnh.
 */
export const surveyRequestReportApi = {
  get: (id: number) => apiGet<SurveyRequestReport>(base(id)),

  /** Khởi tạo khung mặc định (5 giai đoạn mẫu + nút theo dòng hàng). Idempotent. */
  init: (id: number) => apiPost<SurveyRequestReport>(`${base(id)}/init`, {}),

  /** Xóa CẢ khối báo cáo — có thể hoàn tác từ Lịch sử thao tác. */
  deleteAll: (id: number) => apiDelete<SurveyRequestReport>(base(id)),
  /** Hoàn tác lần xóa gần nhất — dựng lại khối từ ảnh chụp. */
  restore: (id: number) => apiPost<SurveyRequestReport>(`${base(id)}/restore`, {}),

  createItem: (id: number, name: string) =>
    apiPost<SurveyRequestReport>(`${base(id)}/items`, { name }),
  renameItem: (id: number, itemId: number, name: string) =>
    apiPatch<SurveyRequestReport>(`${base(id)}/items/${itemId}`, { name }),
  /** Xóa nút — hồ sơ đang gắn nút chuyển về «Chung», không bị xóa lây. */
  deleteItem: (id: number, itemId: number) =>
    apiDelete<SurveyRequestReport>(`${base(id)}/items/${itemId}`),

  createPhase: (id: number, name: string, location: string) =>
    apiPost<SurveyRequestReport>(`${base(id)}/phases`, { name, location }),
  updatePhase: (id: number, phaseId: number, name: string, location: string) =>
    apiPatch<SurveyRequestReport>(`${base(id)}/phases/${phaseId}`, { name, location }),
  /** Backend CHẶN xóa giai đoạn còn hồ sơ — chuyển hồ sơ đi trước. */
  deletePhase: (id: number, phaseId: number) =>
    apiDelete<SurveyRequestReport>(`${base(id)}/phases/${phaseId}`),

  createDoc: (id: number, payload: ReportDocPayload) =>
    apiPost<SurveyRequestReport>(`${base(id)}/docs`, payload),
  /** Gửi trường nào đổi trường đó — nút ✓ chỉ gửi mỗi `status`. */
  updateDoc: (id: number, docId: number, payload: Partial<ReportDocPayload>) =>
    apiPatch<SurveyRequestReport>(`${base(id)}/docs/${docId}`, payload),
  deleteDoc: (id: number, docId: number) =>
    apiDelete<SurveyRequestReport>(`${base(id)}/docs/${docId}`),
}
