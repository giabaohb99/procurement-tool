import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { usageProfileApi } from '../api/usage-profile-api'

/** Hồ sơ một người. `userId` không hợp lệ (NaN, ≤ 0) thì không gọi. */
export function useUsageProfile(userId: number, weeks: number) {
  return useQuery({
    queryKey: queryKeys.report.usageProfile(userId, weeks),
    queryFn: () => usageProfileApi.detail(userId, weeks),
    enabled: Number.isInteger(userId) && userId > 0,
  })
}
