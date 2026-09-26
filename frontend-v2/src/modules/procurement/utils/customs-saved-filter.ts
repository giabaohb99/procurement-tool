// bao-CR-496 — hai hàm thuần nối bộ lọc đã lưu với thanh địa chỉ của màn Tra cứu giá hải quan.
//
// Bộ lọc lưu NGUYÊN chuỗi tham số URL (đại ca chốt: gọn nhất, thêm ô lọc mới không phải
// migration). Chỉ những tham số thuộc danh sách ô lọc mới được ghi / đọc — `page`, `tab`,
// `sort`… của trang không đi theo bộ lọc, và một chuỗi lạ dán vào DB không ghi được khóa lạ
// lên URL.

/** Rút các ô lọc đang áp trên URL thành chuỗi ổn định (khóa xếp theo danh sách, bỏ ô trống). */
export function collectFilterParams(
  searchParams: URLSearchParams,
  filterNames: readonly string[],
): string {
  const out = new URLSearchParams()
  for (const name of filterNames) {
    const values = searchParams.getAll(name).filter((v) => v !== '')
    for (const v of values) out.append(name, v)
  }
  return out.toString()
}

/**
 * Chuỗi đã lưu → bản đồ đưa cho `setUrlParams`: ô có trong bộ lọc nhận giá trị, ô KHÔNG có
 * nhận `null` (xóa khỏi URL) — chọn bộ lọc là màn hình về ĐÚNG trạng thái đó, không cộng
 * dồn với điều kiện đang áp. Tham số nhiều giá trị (lọc nhiều NCC) nối bằng dấu phẩy vì
 * `setUrlParams` chỉ nhận một chuỗi mỗi khóa.
 */
export function parseFilterParams(
  params: string,
  filterNames: readonly string[],
): Record<string, string | null> {
  const saved = new URLSearchParams(params)
  const out: Record<string, string | null> = {}
  for (const name of filterNames) {
    const values = saved.getAll(name).filter((v) => v !== '')
    out[name] = values.length ? values.join(',') : null
  }
  if (out.date_from) out.date_from = expandMonthToDay(out.date_from, 'start')
  if (out.date_to) out.date_to = expandMonthToDay(out.date_to, 'end')
  return out
}

/**
 * bao-CR-502 — bản cũ lọc theo THÁNG tới 26/09/2026 nên bộ lọc lưu từ đó mang «YYYY-MM», mà ô
 * khoảng ngày chỉ đọc «YYYY-MM-DD»: bảng vẫn lọc (backend hiểu cả hai) nhưng ô trông như trống.
 * Đổi ra ngày đầu / cuối tháng — cùng khoảng backend vẫn áp, nên kết quả không đổi.
 */
export function expandMonthToDay(value: string, edge: 'start' | 'end'): string {
  const match = /^(\d{4})-(\d{2})$/.exec(value)
  if (!match) return value
  const [, year, month] = match
  if (Number(month) < 1 || Number(month) > 12) return value
  if (edge === 'start') return `${year}-${month}-01`
  const lastDay = new Date(Number(year), Number(month), 0).getDate()
  return `${year}-${month}-${String(lastDay).padStart(2, '0')}`
}

/** Bộ lọc đã lưu có khớp điều kiện đang áp không — để bày «đang dùng» / «Cập nhật». */
export function sameFilterParams(a: string, b: string, filterNames: readonly string[]): boolean {
  return (
    collectFilterParams(new URLSearchParams(a), filterNames) ===
    collectFilterParams(new URLSearchParams(b), filterNames)
  )
}
