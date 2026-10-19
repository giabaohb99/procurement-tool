import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { usageProfileApi, type UsageListParams } from '../api/usage-profile-api'

export function useUsageProfileList(params: UsageListParams) {
  return useQuery({
    queryKey: queryKeys.report.usageProfileList(params),
    queryFn: () => usageProfileApi.list(params),
    placeholderData: keepPreviousData,
  })
}
