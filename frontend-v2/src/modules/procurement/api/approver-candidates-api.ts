import { apiGet } from '@/core/api'

import type { DeptHeadCandidate } from '../types/purchase-request-detail'

/**
 * bao-CR-499 — người DUYỆT ĐƯỢC chứng từ, nguồn cho ô "Trưởng phòng phê duyệt". Backend hỏi đúng
 * luật phạm vi duyệt, không phụ thuộc quyền xem danh mục nhân sự của người đang lập.
 * bao-CR-552 (01/10/2026): mọi người duyệt được TRỪ tài khoản Quản trị hệ thống, LUÔN kèm Trưởng
 * bộ phận — nên phòng không có trưởng phòng duyệt theo phòng (vd IT) vẫn chọn được.
 */
export type ApproverDocPath = 'purchase-requests' | 'survey-requests' | 'purchase-orders'

export interface ApproverDraftScope {
  department: string
  department_id: number
  company_id: number
  handler_dept_id: number
  /** bao-CR-552: Trưởng bộ phận đang chọn trên form — backend luôn đưa người này vào danh sách. */
  head_of_dept_id?: number
}

/** Danh sách người duyệt được; `default_employee_id` chỉ ĐMH đang lập trả (bao-CR-786). */
export interface ApproverCandidatesResult {
  items: DeptHeadCandidate[]
  default_employee_id?: number
  /** bao-CR-787: mặc định của đơn tạo thẳng theo người lập (công ty, phòng xử lý thật sẽ lưu). */
  default_company_id?: number
  default_handler_dept_id?: number
  default_handler_dept_name?: string
}

export function fetchApproverCandidates(doc: ApproverDocPath, id: number) {
  return apiGet<ApproverCandidatesResult>(`/api/${doc}/${id}/approver-candidates`)
}

export function fetchDraftApproverCandidates(doc: ApproverDocPath, scope: ApproverDraftScope) {
  //  bao-CR-786: ĐMH trả thêm `default_employee_id` — trưởng phòng của phòng trên form, để điền sẵn đơn tạo thẳng.
  return apiGet<ApproverCandidatesResult>(`/api/${doc}/meta/approver-candidates`, {
    params: scope,
  })
}
