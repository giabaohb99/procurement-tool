import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { featureUsageApi, type FeatureUsageParams } from '../api/feature-usage-api'

export function useFeatureUsage(params: FeatureUsageParams) {
  return useQuery({
    queryKey: queryKeys.report.featureUsage(params),
    queryFn: () => featureUsageApi.summary(params),
    placeholderData: keepPreviousData,
  })
}

/** Chi tiết một chức năng theo phòng ban — chỉ gọi khi có chức năng được chọn. */
export function useFeatureBreakdown(params: FeatureUsageParams | null) {
  return useQuery({
    queryKey: queryKeys.report.featureUsageBreakdown(params ?? {}),
    queryFn: () => featureUsageApi.breakdown(params as FeatureUsageParams),
    enabled: params !== null,
  })
}
