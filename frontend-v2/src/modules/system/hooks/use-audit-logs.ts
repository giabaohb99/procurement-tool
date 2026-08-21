import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { auditLogApi, type AuditLogListParams } from '../api/audit-log-api'

export function useAuditLogs(params: AuditLogListParams) {
  return useQuery({
    queryKey: queryKeys.system.auditLogs(params as Record<string, unknown>),
    queryFn: () => auditLogApi.list(params),
    placeholderData: (previousData) => previousData,
    staleTime: 10 * 1000,
  })
}
