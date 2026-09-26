import { apiGet } from '@/core/api'

import type { DeptHeadCandidate } from '../types/purchase-request-detail'

/**
 * bao-CR-499 — người DUYỆT ĐƯỢC chứng từ, nguồn cho ô «Trưởng phòng phê duyệt» (đại ca chốt
 * 26/09/2026: chỉ người duyệt được phiếu đó). Backend hỏi đúng luật phạm vi duyệt, không phụ
 * thuộc quyền xem danh mục nhân sự của người đang lập.
 */
export type ApproverDocPath = 'purchase-requests' | 'survey-requests' | 'purchase-orders'

export interface ApproverDraftScope {
  department: string
  department_id: number
  company_id: number
  handler_dept_id: number
}

export function fetchApproverCandidates(doc: ApproverDocPath, id: number) {
  return apiGet<{ items: DeptHeadCandidate[] }>(`/api/${doc}/${id}/approver-candidates`)
}

export function fetchDraftApproverCandidates(doc: ApproverDocPath, scope: ApproverDraftScope) {
  return apiGet<{ items: DeptHeadCandidate[] }>(`/api/${doc}/meta/approver-candidates`, {
    params: scope,
  })
}
