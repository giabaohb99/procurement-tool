import { useQuery } from '@tanstack/react-query'

import { apiGet } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'

import type { UsageMetricCatalogResponse } from '../types/usage-metric-catalog'

export function useUsageMetricCatalog() {
  return useQuery({
    queryKey: queryKeys.report.usageMetricCatalog(),
    queryFn: () => apiGet<UsageMetricCatalogResponse>('/api/usage-profiles/metrics'),
  })
}
