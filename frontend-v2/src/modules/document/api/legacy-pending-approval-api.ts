import { apiGet } from '@/core/api'
import type { LegacyDecision, LegacyPendingDocument } from '../types/legacy-pending-approval'

export const legacyPendingApprovalApi = {
  list: () => apiGet<LegacyPendingDocument[]>('/api/document-approvals/legacy-pending'),
  decisions: (days: number) =>
    apiGet<LegacyDecision[]>('/api/document-approvals/legacy-decisions', { params: { days } }),
}
