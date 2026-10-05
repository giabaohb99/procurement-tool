import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { workScheduleApi } from '../api/work-schedule-api'
import type { WorkRosterParams } from '../types/work-roster'

/**
 * Lưới «ai làm, ai nghỉ». `keepPreviousData`: bấm sang tuần sau thì lưới cũ ở lại
 * (mờ đi) thay vì chớp trắng. Không thử lại khi lỗi — 422 (quá 42 ngày) hay 403
 * thử lại cũng không khác đi. Luôn nạp lại khi mở màn: xem ghi chú ở `staleTime`.
 */
export function useWorkRoster(params: WorkRosterParams, options: { enabled?: boolean } = {}) {
  return useQuery({
    queryKey: queryKeys.hr.workRoster({ ...params }),
    queryFn: () => workScheduleApi.getRoster(params),
    placeholderData: keepPreviousData,
    retry: false,
    //  Lưới này dẫn xuất từ Gán lịch / Mẫu lịch / đơn nghỉ — ba nơi mà màn khác sửa. Các mutation CRUD
    //  chỉ dọn khóa ['crud', apiPath] nên khóa roster không bị đụng; thay vì móc thêm vào lớp CRUD dùng
    //  chung, buộc roster luôn nạp lại khi màn được mở lại (placeholder vẫn giữ lưới cũ nên không chớp).
    staleTime: 0,
    refetchOnMount: 'always',
    enabled: options.enabled ?? true,
  })
}
