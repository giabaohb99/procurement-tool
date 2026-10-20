/**
 * Đọc/ghi ô GIỜ của panel chi tiết (duoc-CR-656). Tách khỏi component để `react-refresh` không phàn nàn
 * và để kiểm thẳng, không cần dựng giao diện.
 */

/** `"4.50"` → `"4.5"`; rỗng/`null` → `""`. Đưa vào ô nhập cho người đọc, không có số 0 thừa. */
export function formatHours(value: string | null): string {
  if (value === null || value === '') return ''
  const n = Number(value)
  return Number.isFinite(n) ? String(n) : ''
}

/** Đọc ô giờ: rỗng → `0` (xóa giờ), sai → `null` (bỏ qua), hợp lệ → chuỗi số. Trần 999 khớp backend. */
export function parseHours(text: string): string | null {
  const t = text.trim().replace(',', '.')
  if (t === '') return '0'
  if (!/^\d{1,3}(\.\d{1,2})?$/.test(t)) return null
  const n = Number(t)
  return n >= 0 && n <= 999 ? String(n) : null
}
