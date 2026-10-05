import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { workScheduleApi } from '../api/work-schedule-api'

/**
 * Lịch làm việc đang áp cho một nhân sự — thẻ trên hồ sơ.
 * `employeeId <= 0` thì KHÔNG gọi API (hồ sơ chưa tạo / id hỏng). Không thử lại
 * khi lỗi: 404 (ngoài phạm vi) hay 403 thử lại cũng không khác đi.
 */
export function useEffectiveWorkSchedule(employeeId: number) {
  return useQuery({
    queryKey: queryKeys.hr.workScheduleEffective(employeeId),
    queryFn: () => workScheduleApi.getEffective(employeeId),
    enabled: Number.isInteger(employeeId) && employeeId > 0,
    retry: false,
  })
}
