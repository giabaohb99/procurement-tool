import { useQuery } from '@tanstack/react-query'

import { apiGet } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'
import type { DocumentDashboard } from '../types/document-dashboard'

/** Số liệu trang tổng quan Văn thư. Một lần gọi cho cả trang. */
export function useDocumentDashboard() {
  return useQuery({
    queryKey: queryKeys.document.dashboard(),
    queryFn: () => apiGet<DocumentDashboard>('/api/documents/dashboard'),
  })
}
