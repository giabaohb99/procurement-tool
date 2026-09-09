/**
 * Phép chia DÒNG trong một ô lịch tháng — tách khỏi component để kiểm được
 * bằng test mà không phải dựng cả lưới 42 ô.
 */

/**
 * Số dòng nội dung mặc định nằm DƯỚI con số ngày trong một ô — dùng khi chưa đo
 * được chiều cao thật (lượt vẽ đầu tiên).
 *
 * Ứng với ô cao ~95px: cửa sổ 900px, trừ phần đầu trang, chia đều sáu hàng.
 */
export const MONTH_CELL_CONTENT_LINES = 3

/**
 * Chiều cao một dòng chip — **đo trên bản chạy**, không suy từ cỡ chữ: chữ 11px
 * `leading-4` (16) + `py-0.5` (4) + viền (2) + khe `gap-0.5` (2) = 24px.
 */
const LINE_HEIGHT = 24

/**
 * Hàng con số ngày + đệm TRÊN của ô: 16 + 2 (khe) + 4 (`p-1`) = 22px.
 *
 * ⚠️ Cố ý **không cộng đệm DƯỚI**: chip cuối được phép nằm sát đáy ô, đúng lối
 * Google Calendar (nó cũng xếp kín tới pixel cuối). Cộng thêm 4px đó thì màn
 * 1440×900 — ô 96px, vừa khít ba chip — bị tính thành hai dòng và chừa lại một
 * khoảng trắng bằng đúng một chip trong MỌI ô của lưới.
 */
const DAY_ROW_HEIGHT = 22

/**
 * Ô cao `cellHeight` px thì chứa được mấy dòng chip.
 *
 * ⚠️ **Phải ĐO, không được đặt cứng.** Chiều cao ô = (chiều cao khung − đầu
 * trang) ÷ 6, nên nó đổi theo cửa sổ: ~105px trên màn 1440×900 (3 dòng) nhưng
 * chỉ ~79px trên laptop 1280×800 (2 dòng). Đặt cứng 3 dòng thì laptop thấp bày
 * ra chip thứ ba **bị đường kẻ ô cắt ngang** — đúng lỗi ảnh báo 09/09/2026.
 *
 * Sàn 2 dòng: hẹp hơn nữa thì ô không đủ chỗ cho cả «+N người nữa», mà mất dòng
 * đó là mất lối duy nhất đọc tên những người bị giấu. Cửa sổ thấp tới mức đó thì
 * chấp nhận cắt — `overflow-hidden` của ô lo phần còn lại.
 */
export function monthCellLinesFor(cellHeight: number): number {
  const usable = cellHeight - DAY_ROW_HEIGHT
  return Math.max(2, Math.floor(usable / LINE_HEIGHT))
}

/**
 * Ô bày được mấy chip người nghỉ, và giấu mấy người.
 *
 * ⚠️ **Dòng «+N người nữa» CHIẾM CHỖ của một chip**, không cộng thêm vào. Vẽ đủ
 * ba chip rồi thêm dòng "+N" là năm dòng trong một ô bốn dòng: dòng cuối bị
 * đường kẻ ô cắt ngang, mà nó chính là lối duy nhất để đọc tên những người bị
 * giấu — đúng lúc một ngày đông người nghỉ mới là lúc cần tới nó.
 *
 * ⚠️ Ngày lễ cũng ăn một dòng (nó là chip đầu tiên trong ô), nên phải trừ ra:
 * không trừ thì ngày lễ có người nghỉ luôn tràn đúng một dòng.
 */
export function splitMonthCellLines(
  total: number,
  hasHoliday: boolean,
  lines: number = MONTH_CELL_CONTENT_LINES,
): { visible: number; hidden: number } {
  const room = lines - (hasHoliday ? 1 : 0)
  if (total <= room) return { visible: total, hidden: 0 }

  //  `Math.max(…, 0)`: ngày lễ + ô quá thấp có thể đẩy `room` về 1, và lúc đó
  //  bày 0 chip + «+N người nữa» vẫn đúng hơn là bày một chip rồi nuốt phần dư.
  const visible = Math.max(room - 1, 0)
  return { visible, hidden: total - visible }
}

/**
 * Chữ trên con số ngày.
 *
 * ⚠️ **Ngày 1 kèm tên tháng** («1 thg 10») — lối của Google Calendar, và ở lưới
 * này nó giải đúng một chỗ mù: hàng cuối bày 1…11 của tháng sau, chữ mờ thôi
 * không đủ nói đó là tháng nào. Hôm nay thì chỉ để con số: nhãn nằm trong một
 * vòng tròn 24px, nhét thêm «thg 10» vào là vòng tròn méo thành viên thuốc.
 */
export function monthCellDayLabel(date: Date, today: boolean): string {
  if (date.getDate() === 1 && !today) return `1 thg ${date.getMonth() + 1}`
  return String(date.getDate())
}
