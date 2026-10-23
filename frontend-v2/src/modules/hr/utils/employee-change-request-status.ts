import { EMPLOYEE_CHANGE_REQUEST_STATUS, labelOf } from '@/shared/constants/statuses'

/**
 * Mã trạng thái đề nghị sửa hồ sơ (duoc-CR-676). Nhãn đọc từ bộ mã SINH TỪ BACKEND
 * (`EMPLOYEE_CHANGE_REQUEST_STATUS`); ở đây chỉ đặt tên cho bốn con số để mã nguồn khỏi rải
 * `status === 1`. Số đã cấp không bao giờ đổi (luật của `hr_change_request_codes.py`).
 */
export const CHANGE_REQUEST_STATUS = {
  PENDING: 1,
  APPROVED: 2,
  REJECTED: 3,
  WITHDRAWN: 4,
} as const

/** Nhãn của một mã; mã lạ thì trả nguyên số để vẫn thấy được có chuyện gì. */
export function getChangeRequestStatusLabel(status: number): string {
  return labelOf(EMPLOYEE_CHANGE_REQUEST_STATUS, String(status)) || String(status)
}
