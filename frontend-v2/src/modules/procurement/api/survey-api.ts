import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { SurveyDetail, SurveyLine, SurveyTable } from '../types/survey-detail'

const BASE_URL = '/api/surveys'

/** Đầu phiếu + hai bảng dòng gửi lên khi tạo / sửa phiếu khảo sát. */
export interface SurveyPayload {
  pr_code: string
  survey_request_id: number
  sr_code: string
  received_date: string
  result_due_date: string
  item_group: string
  main_content: string
  requirement_detail: string
  request_qty: number
  nspt: string
  has_product_code: boolean
  item_code: string
  item_name: string
  uom: string
  proposed_rate: number
  supplier_lines: SurveyLine[]
  product_lines: SurveyLine[]
}

/** Một dòng trong lần chốt duyệt của TP/QL. */
export interface SurveyLineApproveItem {
  id: number
  line_approve: string
  line_approve_note: string
}

/**
 * Tầng API của Phiếu khảo sát.
 *
 * Luồng: `draft` → submit → `submitted` → approve → `approved`.
 * Nhánh phụ: reject (`rejected`, còn sửa được), cancel (`cancelled`, khóa hẳn —
 * chỉ bấm được khi phiếu đang `submitted`).
 */
export const surveyApi = {
  getById: (id: number) => apiGet<SurveyDetail>(`${BASE_URL}/${id}`),

  create: (payload: SurveyPayload) => apiPost<SurveyDetail>(BASE_URL, payload),

  update: (id: number, payload: SurveyPayload) =>
    apiPatch<SurveyDetail>(`${BASE_URL}/${id}`, payload),

  clone: (id: number) => apiPost<SurveyDetail>(`${BASE_URL}/${id}/clone`, {}),

  /** Backend chặn xóa phiếu đã gửi: chỉ nháp / bị trả lại / đã từ chối mới xóa được. */
  remove: (id: number) => apiDelete<null>(`${BASE_URL}/${id}`),

  submit: (id: number) => apiPost<SurveyDetail>(`${BASE_URL}/${id}/submit`, {}),
  approve: (id: number) => apiPost<SurveyDetail>(`${BASE_URL}/${id}/approve`, {}),

  /** Trả lại để sửa — phiếu về `rejected`, người khảo sát gửi lại được. */
  reject: (id: number, reason: string) =>
    apiPost<SurveyDetail>(`${BASE_URL}/${id}/reject`, { reason }),

  /** Từ chối hẳn. Lý do lưu vào `approve_note` (bảng không có cột lý do riêng). */
  cancel: (id: number, reason: string) =>
    apiPost<SurveyDetail>(`${BASE_URL}/${id}/cancel`, { reason }),

  /**
   * TP/QL chốt duyệt theo TỪNG DÒNG, gửi cả hai bảng trong một lượt. Chỉ đụng vào
   * hai ô duyệt — không kèm nội dung dòng, nên duyệt không đè lên phần người
   * khảo sát đang sửa dở.
   */
  lineApprove: (
    id: number,
    supplierLines: SurveyLineApproveItem[],
    productLines: SurveyLineApproveItem[],
  ) =>
    apiPatch<SurveyDetail>(`${BASE_URL}/${id}/line-approve`, {
      supplier_lines: supplierLines,
      product_lines: productLines,
    }),

  /**
   * Bổ sung thông tin cho MỘT dòng sau khi TP/QL báo "Thiếu thông tin" — đường
   * riêng vì lúc đó phiếu đã `submitted`, không sửa cả phiếu được nữa.
   */
  fillLine: (id: number, table: SurveyTable, lineId: number, changes: SurveyLine) =>
    apiPatch<SurveyDetail>(`${BASE_URL}/${id}/lines/${table}/${lineId}/fill`, changes),
}
