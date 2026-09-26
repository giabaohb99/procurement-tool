import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import {
  fetchApproverCandidates,
  fetchDraftApproverCandidates,
  type ApproverDocPath,
  type ApproverDraftScope,
} from '../api/approver-candidates-api'

/**
 * bao-CR-499 — danh sách chọn ô «Trưởng phòng phê duyệt». Chứng từ đã lưu hỏi theo id (đúng
 * phạm vi của chính nó); đang lập thì hỏi theo phòng ban / pháp nhân / phòng xử lý trên form.
 * Chỉ gọi khi ô còn chọn được (`enabled`) — phiếu đã duyệt thì ô khóa, không cần danh sách.
 */
export function useApproverCandidates(
  doc: ApproverDocPath,
  id: number,
  scope: ApproverDraftScope,
  enabled: boolean,
) {
  return useQuery({
    queryKey: queryKeys.procurement.approverCandidates(doc, id, id ? {} : { ...scope }),
    queryFn: () =>
      id ? fetchApproverCandidates(doc, id) : fetchDraftApproverCandidates(doc, scope),
    enabled: enabled && (id > 0 || Boolean(scope.department || scope.department_id)),
    staleTime: 60_000,
  })
}
