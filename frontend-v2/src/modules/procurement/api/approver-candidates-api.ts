import { apiGet } from '@/core/api'

import type { DeptHeadCandidate } from '../types/purchase-request-detail'

/**
 * bao-CR-499 — người DUYỆT ĐƯỢC chứng từ, nguồn cho ô «Trưởng phòng phê duyệt». Backend hỏi đúng
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

export function fetchApproverCandidates(doc: ApproverDocPath, id: number) {
  return apiGet<{ items: DeptHeadCandidate[] }>(`/api/${doc}/${id}/approver-candidates`)
}

export function fetchDraftApproverCandidates(doc: ApproverDocPath, scope: ApproverDraftScope) {
  return apiGet<{ items: DeptHeadCandidate[] }>(`/api/${doc}/meta/approver-candidates`, {
    params: scope,
  })
}
