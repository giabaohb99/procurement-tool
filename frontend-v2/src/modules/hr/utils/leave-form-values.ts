import type { LeaveRequestPayload } from '../api/leave-api'
import { LEAVE_SESSION, isHourlyLeave, type LeaveRequest } from '../types/leave'
import { periodsOf } from './leave-periods'

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

/**
 * Một KHOẢNG NGÀY LIỀN trên form (duoc-CR-683): từ ngày + buổi → đến ngày + buổi.
 * Đơn một khoảng là hình dạng của gần như mọi tờ đơn; «+ Thêm khoảng ngày» mọc thêm hàng.
 */
export interface LeavePeriodValue {
  from_date: string
  from_session: number
  to_date: string
  to_session: number
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
  /**
   * Con số MÁY tự điền gần nhất vào ô số ngày của đơn MỘT dòng; `null` = chưa có (đơn mới chưa
   * ước lượng, hoặc đơn đã lưu mà số ngày là người dùng gõ đè). Ô số ngày bằng đúng con số này
   * nghĩa là người dùng CHƯA gõ đè — form còn được cập nhật theo ngày, và `toLeavePayload` gửi
   * `days: 0` để backend tự tính (duoc-CR-683 M2: gửi con số ước lượng lên là backend coi như
   * sửa đè và bỏ qua chốt «khoảng 0 ngày công»).
   *
   * Nằm trong giá trị form chứ không trong `useRef` của component: `formValuesOf` cần gieo nó
   * khi mở lại đơn đã lưu (M3), và payload cần đọc nó lúc lưu.
   */
  auto_days: number | null
  /**
   * Các khoảng ngày nghỉ — LUÔN ≥1 hàng. Thay cho bốn ô ngày/buổi ở đầu đơn: đầu đơn nay là
   * bao ngoài do backend dẫn xuất, giữ thêm ở form là nuôi hai nguồn sự thật.
   */
  periods: LeavePeriodValue[]
  /** `HH:MM` — chỉ dùng khi buổi là «Theo giờ» (khi đó đúng MỘT khoảng), rỗng thì không gửi. */
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

/** Đơn khai theo GIỜ — chỉ xảy ra ở đơn một khoảng, nhưng soi mọi hàng cho chắc. */
export function isHourlyForm(values: Pick<LeaveFormValues, 'periods'>): boolean {
  return values.periods.some((p) => isHourlyLeave(p.from_session, p.to_session))
}

/**
 * Bao ngoài của các khoảng — ngày đầu sớm nhất + buổi của nó, ngày cuối muộn nhất + buổi
 * của nó. Đúng luật `request_periods.header_of` (khoảng đầu ↔ khoảng cuối sau khi sắp).
 */
export function outerRangeOf(periods: LeavePeriodValue[]): LeavePeriodValue {
  const filled = periods.filter((p) => p.from_date && p.to_date)
  if (filled.length === 0) {
    return periods[0] ?? { from_date: '', from_session: 1, to_date: '', to_session: 1 }
  }
  const first = filled.reduce((a, b) => (b.from_date < a.from_date ? b : a))
  const last = filled.reduce((a, b) => (b.to_date > a.to_date ? b : a))
  return {
    from_date: first.from_date,
    from_session: first.from_session,
    to_date: last.to_date,
    to_session: last.to_session,
  }
}

export function emptyLeaveForm(): LeaveFormValues {
  const today = todayISO()
  return {
    employee_id: 0,
    employee_name: '',
    //  MỘT dòng trống sẵn: gần như mọi tờ đơn chỉ có một loại nghỉ, nên bắt
    //  người dùng bấm «Thêm loại nghỉ» trước khi gõ được gì là thừa một nhịp.
    lines: [{ leave_type_id: 0, days: 0 }],
    auto_days: null,
    periods: [
      {
        from_date: today,
        from_session: LEAVE_SESSION.FULL,
        to_date: today,
        to_session: LEAVE_SESSION.FULL,
      },
    ],
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

/**
 * Số ngày của đơn đã lưu có phải con số MÁY tính không (duoc-CR-683 M3) — trả chính con số đó
 * để gieo `auto_days`, không thì `null` (người dùng đã gõ đè, giữ nguyên như trước).
 *
 * Chỉ nhận ra được ở đơn MỘT dòng từ HAI khoảng trở lên: backend lưu số ngày từng khoảng là con
 * số máy tính kể cả khi dòng bị gõ đè, nên dòng = tổng các khoảng ⇔ chưa gõ đè.
 * ⚠️ Đơn MỘT khoảng thì backend lưu ngày của khoảng = tổng dòng (`resolve_period_days`), nên
 * phép so luôn đúng và không nói được gì — gieo ở đó là tái phát lỗi NP025 (05/09/2026: gõ 4,
 * mở lại bị đè thành 3). Đơn một khoảng để form tự đối chiếu với con số ước lượng đầu tiên.
 */
function savedAutoDays(lines: LeaveLineValue[], periods: { days: number }[]): number | null {
  if (lines.length !== 1 || periods.length < 2) return null
  const sum = Math.round(periods.reduce((acc, p) => acc + (p.days || 0), 0) * 100) / 100
  return lines[0].days === sum ? sum : null
}

export function formValuesOf(request: LeaveRequest): LeaveFormValues {
  //  Đơn cũ chưa có bản kê (dữ liệu trước 07/09/2026 mà backfill bỏ qua vì
  //  `total_days = 0`) thì dựng lại một dòng từ hai cột đầu đơn — mở ra sửa vẫn
  //  thấy đúng loại nghỉ mình đã chọn, không phải một bảng trống.
  const lines = (request.lines ?? []).map((line) => ({
    leave_type_id: line.leave_type_id,
    days: line.days,
  }))
  const formLines = lines.length
    ? lines
    : [{ leave_type_id: request.leave_type_id, days: request.total_days }]
  //  Qua `periodsOf`: bản dump thiếu `periods` (đơn cũ, tab trình duyệt cũ) rơi về MỘT
  //  khoảng dựng từ đầu đơn — mở ra sửa vẫn thấy đúng hai đầu ngày đã lưu.
  const periods = periodsOf(request)
  return {
    employee_id: request.employee_id,
    employee_name: request.employee_name ?? '',
    lines: formLines,
    auto_days: savedAutoDays(formLines, periods),
    periods: periods.map((p) => ({
      from_date: p.from_date,
      from_session: p.from_session,
      to_date: p.to_date,
      to_session: p.to_session,
    })),
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
 *
 * `periods` gửi ĐỦ danh sách (backend ghi đè, đầu đơn tự dẫn xuất). Bốn ô ngày/buổi đầu đơn
 * vẫn gửi kèm = bao ngoài của các khoảng: backend có `periods` thì bỏ qua chúng, còn bản
 * backend chưa có `periods` thì vẫn lưu đúng một đơn một khoảng như cũ.
 */
/**
 * Dòng loại nghỉ gửi lên. Đơn MỘT dòng mà số ngày vẫn là con số máy tự điền (`auto_days`) thì
 * gửi `days: 0` — y như form mới chưa đụng tới — để backend tự tính và giữ chốt «khoảng không có
 * ngày công nào» (duoc-CR-683 M2). Gửi nguyên con số thì backend hiểu là người dùng sửa đè.
 */
function payloadLines(values: LeaveFormValues): LeaveRequestPayload['lines'] {
  const lines = values.lines.filter((line) => line.leave_type_id > 0)
  const untouched = lines.length === 1 && lines[0].days === values.auto_days
  return lines.map((line) => ({
    leave_type_id: line.leave_type_id,
    days: untouched ? 0 : line.days,
  }))
}

export function toLeavePayload(values: LeaveFormValues): LeaveRequestPayload {
  const isHourly = isHourlyForm(values)
  const outer = outerRangeOf(values.periods)
  return {
    employee_id: values.employee_id,
    lines: payloadLines(values),
    periods: values.periods.map((p) => ({
      from_date: p.from_date,
      from_session: p.from_session,
      to_date: p.to_date,
      to_session: p.to_session,
    })),
    from_date: outer.from_date,
    to_date: outer.to_date,
    from_session: outer.from_session,
    to_session: outer.to_session,
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
