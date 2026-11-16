import { HOURS_PER_DAY, MAX_SEGMENTS_PER_DAY, mergeRanges } from './work-shift-hours'

/**
 * Các DÒNG khung giờ của hộp xếp ca (duoc-CR-761, bản đại ca chốt 16/11/2026): mỗi dòng một khung "Từ giờ → Đến giờ"
 * chọn bằng ô chọn giờ tròn. Thuần, không dính React. Dòng giữ nguyên thứ tự người dùng nhập; chỉ SẮP lúc lưu.
 */

export interface ShiftRow {
  /** Khóa ổn định cho React — không gửi lên API. */
  id: string
  start: number
  end: number
}

/** Khung giờ → dòng; `prefix` để khóa của bản điền sẵn không trùng khóa dòng thêm mới. */
export function rangesToRows(ranges: readonly (readonly number[])[], prefix = 'r'): ShiftRow[] {
  return ranges.map(([start, end], i) => ({ id: `${prefix}${i}`, start, end }))
}

/** Dòng → khung gửi API, đã SẮP theo giờ đầu (backend cũng sắp, nhưng gửi đúng thứ tự cho dễ đọc nhật ký). */
export function rowsToSegments(rows: readonly ShiftRow[]): { start_hour: number; end_hour: number }[] {
  return [...rows]
    .sort((a, b) => a.start - b.start || a.end - b.end)
    .map((r) => ({ start_hour: r.start, end_hour: r.end }))
}

/** Số giờ của một dòng (0 nếu dòng sai). */
export function rowHours(row: Pick<ShiftRow, 'start' | 'end'>): number {
  return row.end > row.start ? row.end - row.start : 0
}

/** Tổng giờ THỰC (hợp các dòng hợp lệ): hai khung đang trùng nhau không bị đếm hai lần trong lúc người dùng sửa. */
export function totalRowHours(rows: readonly ShiftRow[]): number {
  return mergeRanges(rows.map((r) => [r.start, r.end])).reduce((sum, [a, b]) => sum + b - a, 0)
}

export interface ShiftRowsValidation {
  /** Câu lỗi theo id dòng — hiện ngay dưới dòng đó. */
  rowErrors: Record<string, string>
  /** Lỗi của cả danh sách (quá số khung). */
  formError: string | null
  valid: boolean
}

/**
 * Kiểm các dòng — cùng luật `shift_rules.normalize_segments` của backend, nói thành câu tiếng Việt chỉ đúng dòng sai:
 * giờ ngoài 00:00–24:00 · Đến ≤ Từ · trùng giờ với khung khác (hai khung CHẠM nhau như 08–10 và 10–12 là hợp lệ) ·
 * quá 12 khung. Số thứ tự "khung N" theo thứ tự đang hiện.
 */
export function validateShiftRows(rows: readonly ShiftRow[]): ShiftRowsValidation {
  const rowErrors: Record<string, string> = {}
  rows.forEach((row, i) => {
    if (!Number.isInteger(row.start) || !Number.isInteger(row.end) || row.start < 0 || row.end > HOURS_PER_DAY) {
      rowErrors[row.id] = 'Khung giờ phải nằm trong 00:00–24:00 (giờ tròn).'
      return
    }
    if (row.end <= row.start) {
      rowErrors[row.id] = 'Giờ kết thúc phải sau giờ bắt đầu.'
      return
    }
    const clash = rows.findIndex(
      (other, j) => j !== i && other.end > other.start && row.start < other.end && other.start < row.end,
    )
    if (clash >= 0) rowErrors[row.id] = `Trùng giờ với khung ${clash + 1}.`
  })
  const formError =
    rows.length > MAX_SEGMENTS_PER_DAY ? `Mỗi ngày tối đa ${MAX_SEGMENTS_PER_DAY} khung giờ — hãy gộp hoặc xóa bớt.` : null
  return { rowErrors, formError, valid: formError === null && Object.keys(rowErrors).length === 0 }
}

/**
 * Khung 1 tiếng cho nút "+ Thêm khung giờ": ngay sau giờ kết thúc MUỘN NHẤT của các dòng; hết chỗ phía sau (đã tới
 * 24:00) thì lấy giờ trống đầu tiên trong ngày. Không còn giờ trống / đủ 12 khung → `null` (nút tắt).
 */
export function nextFreeHourBlock(rows: readonly ShiftRow[]): { start: number; end: number } | null {
  if (rows.length >= MAX_SEGMENTS_PER_DAY) return null
  const busy = (h: number) => rows.some((r) => r.start <= h && h < r.end)
  const after = rows.length > 0 ? Math.max(...rows.map((r) => r.end)) : 8
  for (let h = after; h < HOURS_PER_DAY; h += 1) if (!busy(h)) return { start: h, end: h + 1 }
  for (let h = 0; h < HOURS_PER_DAY; h += 1) if (!busy(h)) return { start: h, end: h + 1 }
  return null
}

/** Giờ chọn được ở ô "Từ": 00:00 … 23:00. */
export const START_HOUR_OPTIONS = Array.from({ length: HOURS_PER_DAY }, (_, h) => h)

/** Giờ chọn được ở ô "Đến" của một dòng: chỉ SAU giờ "Từ", tới 24:00. */
export function endHourOptions(start: number): number[] {
  const from = Math.min(Math.max(start + 1, 1), HOURS_PER_DAY)
  return Array.from({ length: HOURS_PER_DAY - from + 1 }, (_, i) => from + i)
}

/**
 * Đổi giờ "Từ" của một dòng: giờ "Đến" cũ không còn sau giờ mới thì đẩy theo, GIỮ độ dài khung cũ nếu vừa trong
 * ngày (đổi 08:00→14:00 của khung 2 tiếng ra 14:00–16:00), không thì kẹp ở 24:00.
 */
export function withStartHour(row: ShiftRow, start: number): ShiftRow {
  if (row.end > start) return { ...row, start }
  const length = Math.max(1, row.end - row.start)
  return { ...row, start, end: Math.min(HOURS_PER_DAY, start + length) }
}

/**
 * Hai số tóm tắt của hộp xếp ca: tổng giờ (hợp các khung) và công. Ngày có khung = 1 ngày công dù bao nhiêu giờ (Q3,
 * chốt 16/11/2026); không khung = nghỉ cả ngày, không tính công.
 */
export function shiftTotalStats(rows: readonly ShiftRow[]): { hours: string; workday: string } {
  if (rows.length === 0) return { hours: '0 giờ', workday: 'Không tính' }
  return { hours: `${totalRowHours(rows)} giờ`, workday: '1 ngày' }
}
