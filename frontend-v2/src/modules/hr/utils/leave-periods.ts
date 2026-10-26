import { LEAVE_SESSION, type LeavePeriod, type LeaveRequest } from '../types/leave'

/**
 * KHOẢNG NGÀY CỦA ĐƠN NGHỈ (duoc-CR-683) — nơi DUY NHẤT ở giao diện hiểu "đơn có nhiều khoảng".
 *
 * Mọi chỗ hỏi *"ngày D có nghỉ không"* (Lịch nghỉ, thẻ «Nhìn nhanh») hay hiện thời gian nghỉ
 * phải đi qua đây, KHÔNG so `[from_date, to_date]` ở đầu đơn: đầu đơn là bao ngoài, nuốt cả
 * ngày khe giữa hai khoảng — đơn 27/10 + 03/11→07/11 sẽ hiện nghỉ suốt 28/10→02/11.
 *
 * So ngày bằng CHUỖI `YYYY-MM-DD`: thứ tự từ điển trùng thứ tự thời gian, và không dính
 * chuyện chuỗi ngày trần bị hiểu là mốc UTC rồi lùi một ngày.
 */

/** Hình dạng tối thiểu của một khoảng — dùng chung cho bản ghi API lẫn hàng trên form. */
export interface PeriodLike {
  from_date: string
  from_session: number
  to_date: string
  to_session: number
}

type RequestDates = Pick<
  LeaveRequest,
  'from_date' | 'from_session' | 'to_date' | 'to_session' | 'total_days' | 'periods'
>

/**
 * Các khoảng của tờ đơn. Bản dump thiếu `periods` (tab trình duyệt cũ, đường API chưa gom)
 * thì rơi về MỘT khoảng dựng từ đầu đơn — đúng luật rơi của `period_spans.header_period`.
 */
export function periodsOf(request: RequestDates): LeavePeriod[] {
  if (request.periods && request.periods.length > 0) return request.periods
  return [
    {
      id: 0,
      from_date: request.from_date,
      from_session: request.from_session,
      to_date: request.to_date || request.from_date,
      to_session: request.to_session,
      days: request.total_days,
      sort_order: 0,
    },
  ]
}

export function hasMultiplePeriods(request: RequestDates): boolean {
  return periodsOf(request).length > 1
}

/** Khoảng chứa ngày `iso`, không có thì `undefined` (ngày khe hoặc ngoài đơn). */
export function periodOn(request: RequestDates, iso: string): LeavePeriod | undefined {
  return periodsOf(request).find((p) => p.from_date <= iso && iso <= p.to_date)
}

/** Ngày `iso` có thuộc một khoảng nghỉ của đơn không. */
export function coversDay(request: RequestDates, iso: string): boolean {
  return periodOn(request, iso) !== undefined
}

function dayMonth(iso: string): string {
  const [, m, d] = iso.split('-')
  return `${d}/${m}`
}

function dayMonthYear(iso: string): string {
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

/**
 * Chữ gọn của cả danh sách khoảng — chép đúng luật `period_spans.period_text` ở backend để
 * màn hình, giấy GNP và Trợ lý AI nói cùng một câu: «27/10/2026 · 03/11 (chiều) → 07/11/2026».
 *
 * Năm hiện ở đầu khoảng đầu (và đầu khoảng nào khác năm khoảng đầu), và luôn hiện ở đầu
 * cuối của khoảng nhiều ngày.
 */
export function formatPeriods(periods: PeriodLike[]): string {
  const baseYear = periods[0]?.from_date.slice(0, 4)
  return periods
    .map((p, index) => {
      const withYear = index === 0 || p.from_date.slice(0, 4) !== baseYear
      let start = withYear ? dayMonthYear(p.from_date) : dayMonth(p.from_date)
      if (p.from_session === LEAVE_SESSION.AFTERNOON) start += ' (chiều)'
      if (p.to_date === p.from_date) {
        if (p.to_session === LEAVE_SESSION.MORNING && p.from_session !== LEAVE_SESSION.AFTERNOON) {
          start += ' (sáng)'
        }
        return start
      }
      let end = dayMonthYear(p.to_date)
      if (p.to_session === LEAVE_SESSION.MORNING) end += ' (sáng)'
      return `${start} → ${end}`
    })
    .join(' · ')
}

/** `formatPeriods` cho một tờ đơn. */
export function formatRequestPeriods(request: RequestDates): string {
  return formatPeriods(periodsOf(request))
}

/**
 * Chỉ số các hàng CHỒNG NGÀY với một hàng khác — chép luật `request_periods.check_layout`:
 * sắp theo (từ ngày, đến ngày), hai khoảng kề nhau chồng khi khoảng trước kết thúc từ ngày
 * khoảng sau bắt đầu trở đi. Cùng một ngày sáng + chiều ở hai khoảng cũng tính là chồng.
 *
 * Hàng thiếu ngày bỏ qua: người dùng đang gõ dở, chưa có gì để so.
 */
export function overlappingPeriodIndexes(periods: PeriodLike[]): Set<number> {
  const ordered = periods
    .map((p, index) => ({ p, index }))
    .filter(({ p }) => p.from_date && p.to_date)
    .sort((a, b) =>
      a.p.from_date === b.p.from_date
        ? a.p.to_date.localeCompare(b.p.to_date)
        : a.p.from_date.localeCompare(b.p.from_date),
    )
  const out = new Set<number>()
  //  So mỗi hàng với hàng KẾT THÚC MUỘN NHẤT đứng trước nó, không chỉ với hàng liền trước:
  //  khoảng dài 01→20 nuốt cả 05→06 lẫn 10→12, mà 05→06 và 10→12 thì không chồng nhau.
  let reach: { end: string; index: number } | null = null
  for (const { p, index } of ordered) {
    if (reach && reach.end >= p.from_date) {
      out.add(reach.index)
      out.add(index)
    }
    if (!reach || p.to_date > reach.end) reach = { end: p.to_date, index }
  }
  return out
}

/**
 * Trả số ngày ước lượng về ĐÚNG HÀNG trên form. Backend trả theo thứ tự đã SẮP THEO NGÀY và
 * kèm lại hai đầu ngày — người dùng thì có thể gõ khoảng sau lên trước. Khớp theo cặp
 * (từ ngày, đến ngày); bản trả lời thiếu ngày thì rơi về sắp chỉ số hàng theo cùng luật rồi gán
 * lần lượt. Lệch số phần tử (bản ước lượng của danh sách cũ) thì trả `undefined` thay vì gán
 * nhầm hàng.
 */
export function daysInRowOrder(
  rows: PeriodLike[],
  estimated: { from_date?: string; to_date?: string; days: number }[] | undefined,
): (number | undefined)[] | undefined {
  if (!estimated || estimated.length !== rows.length) return undefined
  if (estimated.every((e) => e.from_date && e.to_date)) {
    const byDates = new Map(estimated.map((e) => [`${e.from_date}|${e.to_date}`, e.days]))
    return rows.map((p) => byDates.get(`${p.from_date}|${p.to_date}`))
  }
  const order = rows
    .map((p, index) => ({ p, index }))
    .sort((a, b) =>
      a.p.from_date === b.p.from_date
        ? a.p.to_date.localeCompare(b.p.to_date)
        : a.p.from_date.localeCompare(b.p.from_date),
    )
  const out: (number | undefined)[] = new Array(rows.length).fill(undefined)
  order.forEach(({ index }, k) => {
    out[index] = estimated[k]?.days
  })
  return out
}

/** `YYYY-MM-DD` cộng `days` ngày, theo lịch ĐỊA PHƯƠNG (không qua UTC). */
export function addDaysISO(iso: string, days: number): string {
  const [y, m, d] = iso.split('-').map(Number)
  const next = new Date(y, m - 1, d + days)
  const mm = `${next.getMonth() + 1}`.padStart(2, '0')
  const dd = `${next.getDate()}`.padStart(2, '0')
  return `${next.getFullYear()}-${mm}-${dd}`
}

/**
 * Rải đơn ra TỪNG NGÀY nó thật sự nghỉ trong cửa sổ `[from, to]` — đi theo KHOẢNG, nên ngày
 * khe giữa hai khoảng không có tên người đó. Cắt theo cửa sổ để đơn nghỉ dài ba tháng không
 * sinh ra chín chục khóa vô ích.
 */
export function groupRequestsByDay<T extends RequestDates>(
  requests: T[],
  from: string,
  to: string,
): Map<string, T[]> {
  const map = new Map<string, T[]>()
  for (const request of requests) {
    //  Một đơn chỉ vào mỗi ngày MỘT lần, kể cả khi dữ liệu lạ có hai khoảng chồng nhau.
    const seen = new Set<string>()
    for (const p of periodsOf(request)) {
      const start = p.from_date > from ? p.from_date : from
      const end = p.to_date < to ? p.to_date : to
      for (let iso = start; iso <= end; iso = addDaysISO(iso, 1)) {
        if (seen.has(iso)) continue
        seen.add(iso)
        const list = map.get(iso)
        if (list) list.push(request)
        else map.set(iso, [request])
      }
    }
  }
  return map
}
