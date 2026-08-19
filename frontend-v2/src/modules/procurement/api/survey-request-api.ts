import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type {
  SurveyRequestDetail,
  SurveyRequestLine,
  SurveyRequestResult,
} from '../types/survey-request-detail'

const BASE_URL = '/api/survey-requests'

/** Phần đầu phiếu + dòng gửi lên khi tạo/sửa YCBG. */
export interface SurveyRequestPayload {
  company_id: number
  requester: string
  requester_id: number
  requester_position: string
  /** CR-086/087 — id là nguồn sự thật; hai cột tên đi kèm chỉ để in. */
  department_id: number
  department: string
  head_of_dept_id: number
  head_of_dept: string
  purpose: string
  request_date: string
  note: string
  lines: Partial<SurveyRequestLine>[]
}

/** YCMH sinh ra từ một lần bấm "Tạo YCMH". */
export interface CreatedPurchaseRequest {
  id: number
  code: string
}

/**
 * Tầng API của phiếu Yêu cầu báo giá.
 *
 * Luồng: `draft` → submit → `submitted` → approve → `processing` (duyệt xong là
 * backend tự chuyển luôn) → thu mua chốt khảo sát → `survey_done` → người YC chọn
 * phương án + tạo YCMH → `pr_created` → finalize → `done`.
 * Nhánh phụ: reject (`rejected`, còn sửa được), cancel (`cancelled`, khóa hẳn).
 */
export const surveyRequestApi = {
  /** Khung NGƯỜI YÊU CẦU: đầu phiếu + dòng, không kèm phương án. */
  getById: (id: number) => apiGet<SurveyRequestDetail>(`${BASE_URL}/${id}`),

  /** Khung KẾT QUẢ: kèm phương án đã bỏ danh tính NCC ngay ở backend. */
  getResult: (id: number) => apiGet<SurveyRequestResult>(`${BASE_URL}/${id}/result`),

  create: (payload: SurveyRequestPayload) => apiPost<SurveyRequestDetail>(BASE_URL, payload),

  update: (id: number, payload: SurveyRequestPayload) =>
    apiPatch<SurveyRequestDetail>(`${BASE_URL}/${id}`, payload),

  /** Khác YCMH: đường dẫn nhân bản của YCBG là `clone`, không phải `copy`. */
  clone: (id: number) => apiPost<SurveyRequestDetail>(`${BASE_URL}/${id}/clone`, {}),

  remove: (id: number) => apiDelete<null>(`${BASE_URL}/${id}`),

  submit: (id: number) => apiPost<SurveyRequestDetail>(`${BASE_URL}/${id}/submit`, {}),
  approve: (id: number) => apiPost<SurveyRequestDetail>(`${BASE_URL}/${id}/approve`, {}),

  /** Trả lại để sửa — phiếu về `rejected`, người YC gửi lại được. */
  reject: (id: number, reason: string) =>
    apiPost<SurveyRequestDetail>(`${BASE_URL}/${id}/reject`, { reason }),
  /** Từ chối hẳn — phiếu về `cancelled` và khóa, phải lập phiếu mới. */
  cancel: (id: number, reason: string) =>
    apiPost<SurveyRequestDetail>(`${BASE_URL}/${id}/cancel`, { reason }),

  /** Chuyển phiếu sang Hoàn thành. */
  finalize: (id: number) => apiPost<SurveyRequestDetail>(`${BASE_URL}/${id}/finalize`, {}),

  /** Gán NSTM phụ trách một dòng. Giá trị là MÃ nhân sự, không phải id. */
  setLineAssignee: (id: number, lineId: number, assignee: string) =>
    apiPatch<SurveyRequestDetail>(`${BASE_URL}/${id}/lines/${lineId}/assignee`, { assignee }),

  /**
   * Người YC chốt trạng thái dòng: '' · 'resurvey' (cần khảo sát lại, backend tự
   * BỎ CHỌN phương án đang chọn) · 'completed'.
   * Đừng nhầm với `PATCH /lines/{id}/status` — endpoint đó đổi cờ `is_completed`
   * của phía thu mua, tên gần giống nhau nhưng khác việc.
   */
  setLineStatus: (id: number, lineId: number, lineStatus: string) =>
    apiPatch<SurveyRequestResult>(`${BASE_URL}/${id}/lines/${lineId}/line-status`, {
      line_status: lineStatus,
    }),

  /** Chọn / bỏ chọn một phương án. Trả luôn khung kết quả mới. */
  chooseOption: (id: number, lineId: number, optionId: number) =>
    apiPatch<SurveyRequestResult>(
      `${BASE_URL}/${id}/lines/${lineId}/options/${optionId}/choose`,
      {},
    ),

  /** Sinh YCMH từ các phương án đã chọn, gom theo NCC. Dòng chưa chọn bị bỏ qua. */
  createPurchaseRequests: (id: number) =>
    apiPost<{ created_prs: CreatedPurchaseRequest[] }>(`${BASE_URL}/${id}/create-prs`, {}),

  /**
   * Trưởng bộ phận của một phòng — người yêu cầu không xem được danh mục Nhân sự.
   * CR-089: ưu tiên `department_id`; tên chỉ là đường lùi cho phòng chưa có id.
   */
  getDeptHead: (department: string, departmentId = 0) =>
    apiGet<{ head_of_dept: string; head_of_dept_id: number }>(`${BASE_URL}/meta/dept-head`, {
      params: { department, department_id: departmentId },
    }),
}
