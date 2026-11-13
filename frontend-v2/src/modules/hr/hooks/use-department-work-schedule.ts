import { useQuery } from '@tanstack/react-query'

import { workScheduleApi } from '../api/work-schedule-api'

//  Khóa CỤC BỘ (ngoại lệ của luật `query-keys.ts`): chỉ hook này dùng, không chỗ nào khác
//  invalidate riêng nó. Đặt dưới tiền tố `['hr', 'work-schedule']` để lệnh quét cả cụm Lịch
//  làm việc vẫn quét trúng. Có nơi thứ hai cần thì dời sang `queryKeys.hr`.
const departmentWorkScheduleKey = (departmentId: number) =>
  ['hr', 'work-schedule', 'effective-department', departmentId] as const

/**
 * Lịch làm việc đang áp cho một phòng ban — tab "Lịch làm việc" ở trang chi tiết phòng ban.
 * `departmentId <= 0` (id hỏng trên URL) thì KHÔNG gọi API. Không thử lại khi lỗi: 403 / 404
 * thử lại cũng không khác đi.
 */
export function useDepartmentWorkSchedule(departmentId: number) {
  return useQuery({
    queryKey: departmentWorkScheduleKey(departmentId),
    queryFn: () => workScheduleApi.getEffectiveForDepartment(departmentId),
    enabled: Number.isInteger(departmentId) && departmentId > 0,
    retry: false,
  })
}
