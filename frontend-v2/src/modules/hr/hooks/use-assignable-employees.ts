import { useQuery } from '@tanstack/react-query'

import { workScheduleApi } from '../api/work-schedule-api'

//  Khóa cục bộ (ngoại lệ của luật khóa tập trung): chỉ hook này dùng, không nơi nào cần làm mới nó từ bên ngoài. Đặt dưới
//  tiền tố ['hr', 'work-schedule'] để làm mới cả nhóm lịch làm việc vẫn quét trúng.
const assignableEmployeesKeys = {
  all: ['hr', 'work-schedule', 'assignable-employees'] as const,
}

/** Một phòng hiếm khi quá vài trăm người; tải một lần rồi ô chọn tự lọc theo chữ gõ. */
const PAGE_SIZE = 1000

/**
 * Nhân sự người đang đăng nhập gán được lịch riêng — nguồn ô Đối tượng ở hộp gán lịch của Trưởng phòng
 * (duoc-CR-757 lượt 2). Danh sách do backend lọc theo phạm vi gán và đã bỏ chính người gọi.
 */
export function useAssignableEmployees(enabled = true) {
  return useQuery({
    queryKey: assignableEmployeesKeys.all,
    queryFn: () => workScheduleApi.listAssignableEmployees({ page_size: PAGE_SIZE }),
    enabled,
    //  Ngắn: nhân sự vừa chuyển phòng phải có / mất mặt khi Trưởng phòng quay lại gán.
    staleTime: 30 * 1000,
  })
}
