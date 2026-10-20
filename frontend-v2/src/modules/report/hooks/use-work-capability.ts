import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { workCapabilityApi, type WorkCapabilityParams } from '../api/work-capability-api'

export function useWorkCapability(params: WorkCapabilityParams) {
  return useQuery({
    queryKey: queryKeys.report.workCapability(params),
    queryFn: () => workCapabilityApi.summary(params),
    placeholderData: keepPreviousData,
  })
}

/** Tải đang ôm — chỉ gọi khi đã chọn pháp nhân hoặc phòng ban (backend từ chối khi không nói rõ phạm vi). */
export function useWorkLoad(params: WorkCapabilityParams | null) {
  return useQuery({
    queryKey: queryKeys.report.workCapabilityLoad(params ?? {}),
    queryFn: () => workCapabilityApi.load(params as WorkCapabilityParams),
    enabled: params !== null,
  })
}
