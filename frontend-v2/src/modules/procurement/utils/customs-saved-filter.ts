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
  return out
}

/** Bộ lọc đã lưu có khớp điều kiện đang áp không — để bày «đang dùng» / «Cập nhật». */
export function sameFilterParams(a: string, b: string, filterNames: readonly string[]): boolean {
  return (
    collectFilterParams(new URLSearchParams(a), filterNames) ===
    collectFilterParams(new URLSearchParams(b), filterNames)
  )
}
