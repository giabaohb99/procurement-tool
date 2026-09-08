import type { LeaveRequest } from '../types/leave'

/**
 * Cách gọi tên phần LOẠI NGHỈ của một tờ đơn, khi đơn khai được nhiều loại
 * (07/09/2026).
 *
 * Hai hàm cho hai chỗ khác nhau, và đừng đổi chỗ cho nhau:
 * · `leaveTypeLabel`  — ô bảng cao 35px, phải gọn;
 * · `leaveLinesText`  — dòng chú thích / tooltip / bản chỉ xem, nói đủ.
 */

/** «Phép năm» · «Phép năm +1» khi đơn còn loại khác. */
export function leaveTypeLabel(request: LeaveRequest): string {
  const lines = request.lines ?? []
  const primary = request.leave_type_name || '—'
  //  Đếm theo BẢN KÊ, không theo `leave_type_name`: đường trả về nào không gom
  //  bản kê thì `lines` rỗng, và lúc đó đơn nhiều loại vẫn hiện tên loại chính —
  //  thiếu chữ «+1» còn hơn hiện «+0» hoặc bịa ra một con số.
  return lines.length > 1 ? `${primary} +${lines.length - 1}` : primary
}

/** «Phép năm 3 ngày · Nghỉ không lương 1 ngày». Rỗng khi không có bản kê. */
export function leaveLinesText(request: LeaveRequest): string {
  return (request.lines ?? [])
    .map((line) => `${line.leave_type_name || `#${line.leave_type_id}`} ${line.days} ngày`)
    .join(' · ')
}

/** Đơn có khai từ hai loại nghỉ trở lên không. */
export function hasMultipleLeaveTypes(request: LeaveRequest): boolean {
  return (request.lines ?? []).length > 1
}
