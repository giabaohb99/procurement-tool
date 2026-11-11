import { LEAVE_STATUS } from '../types/leave'

/**
 * Thứ tự DÒNG ĐỜI của phiếu nội bộ chạy qua bộ máy duyệt: Nháp → Chờ duyệt → Trả về chỉnh sửa → Đã duyệt → Từ chối →
 * Đã hủy. Mã số khai theo thứ tự thêm vào hệ thống (3 Đã duyệt, 4 Từ chối, 5 Trả về) nên xếp thẳng theo số là đặt
 * "Trả về" sau "Từ chối". Khớp `APPROVAL_LIFECYCLE_ORDER` (`backend/app/modules/leave/sort_expressions.py`) và
 * `BOOKING_LIFECYCLE_ORDER` (`meeting_room/sort_expressions.py`) — đơn nghỉ phép, phiếu nghỉ bù, phiếu thanh toán
 * phép và phiếu đặt phòng dùng chung một bộ số (`LEAVE_STATUS` = `LEAVE_COMP_STATUS` = `LEAVE_ENCASHMENT_STATUS` =
 * `ROOM_BOOKING_STATUS`).
 */
const APPROVAL_LIFECYCLE_ORDER: readonly number[] = [
  LEAVE_STATUS.DRAFT,
  LEAVE_STATUS.PENDING,
  LEAVE_STATUS.RETURNED,
  LEAVE_STATUS.APPROVED,
  LEAVE_STATUS.REJECTED,
  LEAVE_STATUS.CANCELLED,
]

/**
 * Hạng dòng đời của một mã trạng thái, dùng cho cột Trạng thái của hàng đợi xếp ở trình duyệt (*Cần tôi duyệt*,
 * *Tôi đã duyệt*) để ra cùng thứ tự với phạm vi xếp tại máy chủ (duoc-CR-748). Thiếu mã ra `null` (ô trống, xuống
 * cuối); mã lạ đứng sau mọi mã đã biết.
 */
export function approvalLifecycleRank(status: number | null | undefined): number | null {
  if (status === null || status === undefined) return null
  const rank = APPROVAL_LIFECYCLE_ORDER.indexOf(status)
  return rank === -1 ? APPROVAL_LIFECYCLE_ORDER.length : rank
}
