/**
 * MỘT bộ so sánh duy nhất cho mọi bảng xếp ngay trên trình duyệt (duoc-CR-744): bảng dòng chứng từ,
 * bảng Tra cứu thị trường, hộp việc nghỉ phép / đặt phòng, văn bản đến, phân công phụ trách...
 * Cùng luật với các bảng xếp tại server (`backend/app/core/sort_order.py`) để một cột xếp ở đâu cũng ra
 * cùng một thứ tự.
 *
 * Luật:
 * - ô TRỐNG (null, undefined, chuỗi rỗng / chỉ khoảng trắng) luôn xuống CUỐI ở cả hai chiều, như Excel;
 *   số 0 và `false` là giá trị thật, không phải ô trống;
 * - boolean so như 0 / 1;
 * - số và chuỗi thuần số (dạng "-12.5", API trả Decimal dạng chuỗi) so theo SỐ: "12.5" > "12.25";
 * - còn lại so theo tiếng Việt (có dấu, không phân biệt hoa thường) và hiểu số trong chữ
 *   ("Option 2" < "Option 10"); ngày "YYYY-MM-DD" so như chữ là đúng thứ tự.
 */

/** Giá trị dùng để so khi xếp một cột. */
export type SortValue = string | number | boolean | null | undefined

export type SortDir = 'asc' | 'desc'

const collator = new Intl.Collator('vi', { numeric: true, sensitivity: 'base' })

/** Chuỗi thuần số (API trả Decimal dạng chuỗi: "12.5", "-3", "1000.000"). */
const NUMERIC_TEXT = /^-?\d+(\.\d+)?$/

function toNumberIfNumeric(value: string | number): number | null {
  if (typeof value === 'number') return value
  return NUMERIC_TEXT.test(value.trim()) ? Number(value) : null
}

/** Ô trống: null, undefined, chuỗi rỗng hoặc chỉ khoảng trắng. */
export function isBlankSortValue(value: SortValue): boolean {
  return value === null || value === undefined || (typeof value === 'string' && value.trim() === '')
}

/** So hai giá trị ĐỀU KHÔNG trống theo chiều TĂNG. */
function compareFilledValues(rawA: SortValue, rawB: SortValue): number {
  //  boolean đổi thành 0 / 1 TRƯỚC khi so, để boolean lẫn với chữ vẫn đi tiếp đường số / chữ
  //  (so thẳng `Number('abc')` ra NaN làm hỏng cả phép sắp xếp).
  const a = typeof rawA === 'boolean' ? Number(rawA) : (rawA as string | number)
  const b = typeof rawB === 'boolean' ? Number(rawB) : (rawB as string | number)
  //  Hai phía đều là SỐ (kể cả chuỗi số) thì so theo số: so chữ "12.5" với "12.25"
  //  theo kiểu hiểu số vẫn ra 5 < 25, tức 12,5 đứng TRƯỚC 12,25.
  const numA = toNumberIfNumeric(a)
  const numB = toNumberIfNumeric(b)
  if (numA !== null && numB !== null) return numA - numB
  return collator.compare(String(a), String(b))
}

/**
 * So hai ô theo chiều `dir`. Ô trống luôn xuống CUỐI ở cả hai chiều: xếp giảm cột Thành tiền mà dòng chưa
 * nhập giá nổi lên đầu là che mất thứ cần xem. Hai ô bằng nhau trả 0 - việc phân thắng bại để người gọi.
 */
export function compareSortValues(a: SortValue, b: SortValue, dir: SortDir = 'asc'): number {
  const blankA = isBlankSortValue(a)
  const blankB = isBlankSortValue(b)
  if (blankA || blankB) return blankA === blankB ? 0 : blankA ? 1 : -1
  const result = compareFilledValues(a, b)
  //  `-0` lọt ra ngoài làm `Object.is(x, 0)` sai, nên bằng nhau thì trả đúng 0.
  return dir === 'asc' || result === 0 ? result : -result
}

/**
 * Trả BẢN SAO đã xếp theo `getValue`, không sửa mảng đầu vào. Giá trị ô lấy MỘT lần cho mỗi dòng.
 *
 * Hai dòng bằng nhau thì gọi `tieBreak` (nhận cặp dòng gốc, KHÔNG đảo theo `dir`); không truyền thì giữ
 * thứ tự gốc (xếp ổn định). Nơi đang cần khóa phụ: hộp việc nghỉ phép / đặt phòng / văn bản đến dùng `id`
 * giảm dần (`byIdDescending`) để phân trang không nhảy dòng; phân công phụ trách dùng phân loại, phòng, id.
 */
export function sortRowsBy<T>(
  rows: readonly T[],
  getValue: (row: T) => SortValue,
  dir: SortDir,
  tieBreak?: (a: T, b: T) => number,
): T[] {
  return rows
    .map((row, index) => ({ row, index, value: getValue(row) }))
    .sort(
      (a, b) =>
        compareSortValues(a.value, b.value, dir) || tieBreak?.(a.row, b.row) || a.index - b.index,
    )
    .map((item) => item.row)
}

/** Khóa phụ chuẩn của các danh sách phân trang: `id` giảm dần để thứ tự không đổi giữa các lần dựng. */
export function byIdDescending(a: { id: number }, b: { id: number }): number {
  return b.id - a.id
}
