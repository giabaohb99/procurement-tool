/**
 * Số ngày quy định (QĐ) có hàng theo Phân loại VTBB/NL — bản sao luật của backend
 * (`app/modules/catalog/lead_time.py`). Sửa một bên thì phải sửa cả hai.
 *
 * Danh mục Phân loại giữ 2 mốc: `std_days` (NCC CÓ sẵn hàng) và `std_days_unavail`
 * (KHÔNG sẵn). Mặc định LUÔN lấy mốc DÀI NHẤT — mốc "không sẵn hàng" — vì lúc tạo
 * phiếu/đơn chưa ai chắc NCC còn hàng; thiếu mốc đó thì lùi về mốc "có sẵn", thiếu
 * cả hai thì 15 ngày.
 */
export const DEFAULT_STD_DAYS = 15

/** Danh mục trả số ngày dưới dạng chuỗi, có phiếu còn kèm chữ ("15 ngày"). */
interface LeadTimeSource {
  name?: string | null
  std_days?: string | number | null
  std_days_unavail?: string | number | null
}

function toInt(value: string | number | null | undefined): number {
  return parseInt(String(value ?? '').replace(/[^\d]/g, ''), 10) || 0
}

/**
 * Khóa tra cứu phân loại: bỏ dấu cách thừa, KHÔNG phân biệt chữ hoa/thường (CR-083).
 * Phân loại trên sản phẩm là chuỗi tự do nên hay lệch hoa/thường so với danh mục
 * ("Nhãn thùng" vs "Nhãn Thùng"); khớp tuyệt đối làm các dòng đó rơi oan về 15 ngày.
 */
export function normalizeGroupName(name: string | null | undefined): string {
  return String(name ?? '')
    .normalize('NFC')
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean)
    .join(' ')
}

/** {tên phân loại đã chuẩn hóa: số ngày QĐ} từ danh mục Phân loại đã nạp sẵn ở màn hình. */
export function buildStdDaysMap(itemGroups: LeadTimeSource[] | undefined): Record<string, number> {
  const map: Record<string, number> = {}
  for (const group of itemGroups ?? []) {
    map[normalizeGroupName(group.name)] =
      toInt(group.std_days_unavail) || toInt(group.std_days) || DEFAULT_STD_DAYS
  }
  return map
}

/** Số ngày QĐ của 1 phân loại; phân loại lạ/để trống cũng ra mốc mặc định. */
export function findStdDays(map: Record<string, number>, itemGroup: string): number {
  return map[normalizeGroupName(itemGroup)] || DEFAULT_STD_DAYS
}

/** 'YYYY-MM-DD' + số ngày → 'YYYY-MM-DD'. Cộng bằng UTC để không lệch 1 ngày vì múi giờ. */
export function addDays(base: string, days: number): string {
  const matched = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(base || '').trim())
  if (!matched || days <= 0) return ''
  const date = new Date(Date.UTC(+matched[1], +matched[2] - 1, +matched[3]))
  if (isNaN(date.getTime())) return ''
  date.setUTCDate(date.getUTCDate() + days)
  return date.toISOString().slice(0, 10)
}

/** Ngày QĐ có hàng = mốc gốc (Ngày tiếp nhận YCMH / Ngày đặt hàng ĐMH) + số ngày QĐ. */
export function calcRegulatedDate(
  map: Record<string, number>,
  itemGroup: string,
  base: string,
): string {
  return addDays(base, findStdDays(map, itemGroup))
}
