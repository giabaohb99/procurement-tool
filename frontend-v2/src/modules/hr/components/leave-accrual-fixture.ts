import type { LeaveAccrualInfo } from '../types/leave'

/**
 * Nhãn y như backend trả ở `accrual_status_label` (`leave/constants.LEAVE_ACCRUAL_STATUS_LABELS`, duoc-CR-762) — CHỈ để
 * bài kiểm dựng dữ liệu giả API. Giao diện không gõ nhãn; đổi nhãn ở backend không cần sửa mã màn hình.
 */
export const API_ACCRUAL_LABELS: Record<number, string> = {
  1: 'Đang tích',
  2: 'Đang thử việc — chưa tích',
  3: 'Chưa có HĐLĐ trên hệ thống',
  4: 'Lịch sử HĐLĐ chưa đủ — đang tính từ ngày vào làm',
  5: 'Hợp đồng dịch vụ / cộng tác viên — không tích phép năm',
  6: 'Chưa tới ngày làm chính thức',
}

/** Ba trường tích phép như API trả cho một người ở mã `status`. */
export function accrualFixture(status: number, startDate: string | null = null): LeaveAccrualInfo {
  return {
    accrual_status: status,
    accrual_status_label: API_ACCRUAL_LABELS[status] ?? null,
    accrual_start_date: startDate,
  }
}
