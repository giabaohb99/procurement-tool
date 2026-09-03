import type { LeaveRequestPayload } from '../api/leave-api'
import { LEAVE_SESSION, type LeaveRequest } from '../types/leave'

/**
 * Giá trị của form đơn nghỉ phép, và ba hàm dựng nó.
 *
 * Tách khỏi `components/leave-request-form.tsx` vì tệp component chỉ được phép
 * export component — `react-refresh/only-export-components` cảnh báo, và cảnh
 * báo đó có lý do thật: nạp nóng (HMR) không thay được một hằng số đứng chung
 * tệp với component, nên sửa mã xong màn hình vẫn chạy bản cũ.
 */

/**
 * Một dòng bàn giao trong form.
 *
 * Giữ thêm `employee_name` mà API KHÔNG cần: người lập đơn phải đọc được tên
 * người mình đã cử ngay cả khi không có quyền `employee.read` để nạp danh bạ
 * (hành chính lập hộ, tài khoản phạm vi hẹp). Không giữ thì mở lại đơn cũ chỉ
 * thấy `#7`. Tên bị lọc bỏ ở `toLeavePayload`, không đẩy lên server.
 */
export interface LeaveHandoverValue {
  employee_id: number
  employee_name: string
  content: string
}

export interface LeaveFormValues {
  leave_type_id: number
  from_date: string
  to_date: string
  from_session: number
  to_session: number
  total_days: number
  reason: string
  contact_phone: string
  contact_address: string
  handovers: LeaveHandoverValue[]
}

export const REASON_MAX = 1000

/** Ngày hôm nay theo giờ ĐỊA PHƯƠNG, dạng `YYYY-MM-DD`.
 *
 * `toISOString()` quy về UTC, mà Việt Nam lệch +7 — mở form lúc 0h-7h sáng thì
 * ô «Từ ngày» hiện ngày HÔM QUA.
 */
function todayISO(): string {
  const d = new Date()
  const m = `${d.getMonth() + 1}`.padStart(2, '0')
  const day = `${d.getDate()}`.padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}

export function emptyLeaveForm(): LeaveFormValues {
  const today = todayISO()
  return {
    leave_type_id: 0,
    from_date: today,
    to_date: today,
    from_session: LEAVE_SESSION.FULL,
    to_session: LEAVE_SESSION.FULL,
    //  `0` = để backend tự tính. Khác 0 nghĩa là người dùng đã sửa đè.
    total_days: 0,
    reason: '',
    contact_phone: '',
    contact_address: '',
    handovers: [],
  }
}

export function formValuesOf(request: LeaveRequest): LeaveFormValues {
  return {
    leave_type_id: request.leave_type_id,
    from_date: request.from_date,
    to_date: request.to_date,
    from_session: request.from_session,
    to_session: request.to_session,
    total_days: request.total_days,
    reason: request.reason,
    contact_phone: request.contact_phone,
    contact_address: request.contact_address,
    handovers: (request.handovers ?? []).map((h) => ({
      employee_id: h.employee_id,
      employee_name: h.employee_name ?? '',
      content: h.content ?? '',
    })),
  }
}

/**
 * Đổi giá trị form thành thân yêu cầu gửi lên API.
 *
 * ⚠️ **Luôn gửi `handovers`, kể cả khi rỗng.** Backend coi "có mặt khóa
 * `handovers`" là lệnh GHI ĐÈ cả danh sách (`_replace_handovers`), còn vắng mặt
 * là "giữ nguyên". Bỏ khóa khi rỗng thì người dùng xóa hết người bàn giao rồi
 * bấm lưu sẽ thấy danh sách cũ hiện lại y nguyên.
 *
 * Dòng chưa chọn người (`employee_id = 0`) bị loại ngay ở đây — backend cũng bỏ
 * qua, nhưng lọc sớm thì thân yêu cầu sạch và log dễ đọc.
 */
export function toLeavePayload(values: LeaveFormValues): LeaveRequestPayload {
  return {
    leave_type_id: values.leave_type_id,
    from_date: values.from_date,
    to_date: values.to_date,
    from_session: values.from_session,
    to_session: values.to_session,
    total_days: values.total_days,
    reason: values.reason,
    contact_phone: values.contact_phone,
    contact_address: values.contact_address,
    handovers: values.handovers
      .filter((h) => h.employee_id > 0)
      .map((h) => ({ employee_id: h.employee_id, content: h.content.trim() })),
  }
}
