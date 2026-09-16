/**
 * Ba kiểu xem của lịch đặt xe — Ngày · Tuần · Tháng.
 *
 * Ngày và Tuần dùng `timeGrid` (CÓ trục giờ) chứ không phải `dayGrid`: việc chính
 * của hai khám đó là xem giờ nào đông xe và chuyến nào trùng giờ nhau, mà
 * `dayGrid` chỉ xếp chip thành danh sách nên không đọc ra được điều đó.
 * Tháng vẫn là `dayGrid` — một tháng không vẽ nổi trục giờ.
 */
export const CALENDAR_VIEWS = [
  { value: 'timeGridDay', label: 'Ngày' },
  { value: 'timeGridWeek', label: 'Tuần' },
  { value: 'dayGridMonth', label: 'Tháng' },
] as const

export type CalendarViewType = (typeof CALENDAR_VIEWS)[number]['value']

/** Khám có trục giờ → chip phải cao theo độ dài chuyến, không cố định 28px. */
export function isTimeGridView(viewType: string): boolean {
  return viewType.startsWith('timeGrid')
}

/**
 * URL ghi kiểu xem bằng chữ NGƯỜI ĐỌC ĐƯỢC (`?mode=day`), không bằng tên khám
 * của FullCalendar (`timeGridDay`).
 *
 * Hai lý do: link gửi cho đồng nghiệp đọc ra nghĩa, và tên khám là chi tiết của
 * thư viện — đổi thư viện dựng lịch thì mọi link cũ chết theo. Cũng đúng bộ chữ
 * mà Lịch nghỉ phép đang dùng (`/hr/leave-calendar?mode=day&date=…`), nên hai
 * màn lịch của hệ thống hành xử giống nhau.
 */
const MODE_TO_VIEW = {
  day: 'timeGridDay',
  week: 'timeGridWeek',
  month: 'dayGridMonth',
} as const satisfies Record<string, CalendarViewType>

export type CalendarMode = keyof typeof MODE_TO_VIEW

/** Kiểu xem lúc chưa ai chọn gì — mở màn ra là thấy cả tháng. */
export const DEFAULT_CALENDAR_MODE: CalendarMode = 'month'

/**
 * `?mode=` → tên khám của FullCalendar. Chữ lạ (người dùng tự sửa URL, link cũ
 * từ bản trước) trả về khám mặc định thay vì để FC nhận một tên không có thật —
 * FC ném lỗi lúc dựng và cả trang trắng.
 */
export function viewFromMode(raw: string | null | undefined): CalendarViewType {
  //  Hỏi `Object.hasOwn` chứ KHÔNG viết `MODE_TO_VIEW[raw] ?? mặc định`: tra
  //  thẳng thì `?mode=constructor` (hay `toString`, `__proto__`) trúng khóa KẾ
  //  THỪA của Object, `??` thấy có giá trị nên trả về nguyên một hàm JS — FC
  //  nhận cái đó làm tên khám là trắng trang.
  if (raw && Object.hasOwn(MODE_TO_VIEW, raw)) return MODE_TO_VIEW[raw as CalendarMode]
  return MODE_TO_VIEW[DEFAULT_CALENDAR_MODE]
}

/** Chiều ngược lại — tên khám FullCalendar → chữ ghi vào URL. */
export function modeFromView(viewType: string): CalendarMode {
  const found = (Object.keys(MODE_TO_VIEW) as CalendarMode[]).find(
    (mode) => MODE_TO_VIEW[mode] === viewType,
  )
  return found ?? DEFAULT_CALENDAR_MODE
}
