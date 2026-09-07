import type { LeaveRequestPayload } from '../api/leave-api'
import { LEAVE_SESSION, isHourlyLeave, type LeaveRequest } from '../types/leave'

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

/**
 * Một dòng loại nghỉ trong form.
 *
 * `days = 0` nghĩa là **chưa có con số** — đơn một dòng thì backend tự tính từ
 * khoảng ngày, đơn nhiều dòng thì backend chặn và đòi nhập rõ.
 */
export interface LeaveLineValue {
  leave_type_id: number
  days: number
}

export interface LeaveFormValues {
  /** NGƯỜI NGHỈ. `0` = chính người đang lập đơn — xem `toLeavePayload`. */
  employee_id: number
  employee_name: string
  /**
   * Bản kê loại nghỉ. **Không có ô `leave_type_id` lẫn `total_days` trong form
   * nữa**: cả hai là con số DẪN XUẤT từ danh sách này (loại chính = dòng nhiều
   * ngày nhất, tổng ngày = tổng các dòng), và backend tự đặt. Giữ chúng ở đây
   * là nuôi hai nguồn sự thật cho cùng một con số, rồi cái thứ hai sẽ lệch.
   */
  lines: LeaveLineValue[]
  from_date: string
  to_date: string
  from_session: number
  to_session: number
  /** `HH:MM` — chỉ dùng khi buổi là «Theo giờ», rỗng thì không gửi lên. */
  from_time: string
  to_time: string
  reason: string
  contact_phone: string
  contact_address: string
  handovers: LeaveHandoverValue[]
}

export const REASON_MAX = 1000

/** Trần số loại nghỉ trong một đơn — khớp `MAX_LINES` ở backend. */
export const MAX_LEAVE_LINES = 10

/** Tổng số ngày của đơn = tổng các dòng. Nguồn DUY NHẤT của con số này ở v2. */
export function totalLeaveDays(lines: LeaveLineValue[]): number {
  //  Làm tròn 2 chữ số vì cộng số thực: 0.13 + 0.5 ra 0.6300000000000001 và ô
  //  «Tổng cộng» hiện nguyên cái đuôi đó ra màn hình.
  return Math.round(lines.reduce((sum, line) => sum + (line.days || 0), 0) * 100) / 100
}

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
    employee_id: 0,
    employee_name: '',
    //  MỘT dòng trống sẵn: gần như mọi tờ đơn chỉ có một loại nghỉ, nên bắt
    //  người dùng bấm «Thêm loại nghỉ» trước khi gõ được gì là thừa một nhịp.
    lines: [{ leave_type_id: 0, days: 0 }],
    from_date: today,
    to_date: today,
    from_session: LEAVE_SESSION.FULL,
    to_session: LEAVE_SESSION.FULL,
    from_time: '',
    to_time: '',
    reason: '',
    contact_phone: '',
    contact_address: '',
    handovers: [],
  }
}

/** `HH:MM:SS` của API → `HH:MM` cho ô nhập giờ. Rỗng khi không khai theo giờ. */
function hhmm(value?: string | null): string {
  return (value ?? '').slice(0, 5)
}

export function formValuesOf(request: LeaveRequest): LeaveFormValues {
  //  Đơn cũ chưa có bản kê (dữ liệu trước 07/09/2026 mà backfill bỏ qua vì
  //  `total_days = 0`) thì dựng lại một dòng từ hai cột đầu đơn — mở ra sửa vẫn
  //  thấy đúng loại nghỉ mình đã chọn, không phải một bảng trống.
  const lines = (request.lines ?? []).map((line) => ({
    leave_type_id: line.leave_type_id,
    days: line.days,
  }))
  return {
    employee_id: request.employee_id,
    employee_name: request.employee_name ?? '',
    lines: lines.length
      ? lines
      : [{ leave_type_id: request.leave_type_id, days: request.total_days }],
    from_date: request.from_date,
    to_date: request.to_date,
    from_session: request.from_session,
    to_session: request.to_session,
    from_time: hhmm(request.from_time),
    to_time: hhmm(request.to_time),
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
 *
 * `lines` cũng vậy: dòng chưa chọn loại nghỉ bị loại. Bảng dòng luôn chừa sẵn
 * một dòng trống để gõ, và đẩy nó lên là ăn câu chặn *"Chưa chọn loại nghỉ"*
 * cho một dòng người dùng còn chưa động tới.
 */
export function toLeavePayload(values: LeaveFormValues): LeaveRequestPayload {
  const isHourly = isHourlyLeave(values.from_session, values.to_session)
  return {
    employee_id: values.employee_id,
    lines: values.lines
      .filter((line) => line.leave_type_id > 0)
      .map((line) => ({ leave_type_id: line.leave_type_id, days: line.days })),
    from_date: values.from_date,
    to_date: values.to_date,
    from_session: values.from_session,
    to_session: values.to_session,
    //  `null` chứ không phải chuỗi rỗng: cột giờ nhận `NULL` khi đơn không khai
    //  theo giờ, và backend chặn nếu có giờ mà buổi lại không phải «Theo giờ».
    from_time: isHourly && values.from_time ? values.from_time : null,
    to_time: isHourly && values.to_time ? values.to_time : null,
    reason: values.reason,
    contact_phone: values.contact_phone,
    contact_address: values.contact_address,
    handovers: values.handovers
      .filter((h) => h.employee_id > 0)
      .map((h) => ({ employee_id: h.employee_id, content: h.content.trim() })),
  }
}
