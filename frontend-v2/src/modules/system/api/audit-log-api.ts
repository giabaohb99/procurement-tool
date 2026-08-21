import { apiGet } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'

export interface SystemAuditLogItem {
  id: number
  entity: string
  entity_id: number
  action: string
  action_label: string
  message: string
  by: string
  by_id: number | null
  at: string
}

export interface AuditLogListParams extends ListParams {
  entity?: string
  entity_id?: number
  action?: string
  search?: string
  created_by?: number
  from_date?: string
  to_date?: string
}

export const auditLogApi = {
  list: (params: AuditLogListParams) =>
    apiGet<PaginatedResult<SystemAuditLogItem>>('/api/audit-logs', { params }),
}
