/**
 * Số ngày quy định (QĐ) có hàng theo Phân loại VTBB/NL — bản sao luật của backend
 * (`app/modules/catalog/lead_time.py`). Sửa một bên thì phải sửa cả hai.
 *
 * Danh mục Phân loại giữ 2 mốc: `std_days` (NCC CÓ sẵn hàng) và `std_days_unavail` (KHÔNG sẵn).
 * Mặc định LUÔN lấy mốc DÀI NHẤT — mốc "không sẵn hàng" — vì lúc tạo phiếu/đơn chưa ai chắc NCC
 * còn hàng; thiếu mốc đó thì lùi về mốc "có sẵn", thiếu cả hai thì 15 ngày.
 */
export const DEFAULT_STD_DAYS = 15

const toInt = (s: any) => parseInt(String(s ?? '').replace(/[^\d]/g, ''), 10) || 0

/** {tên phân loại: số ngày QĐ} từ danh mục Phân loại đã nạp sẵn ở màn hình. */
export function stdDaysMap(itemGroups: any[]): Record<string, number> {
  const m: Record<string, number> = {}
  for (const g of itemGroups || []) {
    m[String(g.name || '').trim()] = toInt(g.std_days_unavail) || toInt(g.std_days) || DEFAULT_STD_DAYS
  }
  return m
}

/** Số ngày QĐ của 1 phân loại; phân loại lạ/để trống cũng ra mốc mặc định. */
export function stdDaysOf(m: Record<string, number>, itemGroup: string): number {
  return m[String(itemGroup || '').trim()] || DEFAULT_STD_DAYS
}

/** 'YYYY-MM-DD' + số ngày → 'YYYY-MM-DD'. Cộng bằng UTC để không lệch 1 ngày vì múi giờ. */
export function addDays(base: string, days: number): string {
  const s = String(base || '').trim()
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(s)
  if (!m || days <= 0) return ''
  const d = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]))
  if (isNaN(d.getTime())) return ''
  d.setUTCDate(d.getUTCDate() + days)
  return d.toISOString().slice(0, 10)
}

/** Ngày QĐ có hàng = mốc gốc (Ngày tiếp nhận YCMH / Ngày đặt hàng ĐMH) + số ngày QĐ. */
export function regulatedDate(m: Record<string, number>, itemGroup: string, base: string): string {
  return addDays(base, stdDaysOf(m, itemGroup))
}
