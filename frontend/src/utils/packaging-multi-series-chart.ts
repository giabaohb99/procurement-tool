/**
 * duoc-CR-784 — số liệu thuần cho biểu đồ NHIỀU ĐƯỜNG của Lịch sử mua hàng (chế độ sản phẩm, đúng một sản phẩm): mỗi mã
 * thành phần của định mức một đường giá. Trục ngang là các NGÀY MUA của mọi đường gộp lại, cách đều nhau như biểu đồ một
 * mã; mỗi đường chỉ nối các ngày nó có giá (không bịa điểm ở ngày không mua).
 */
import type { PackagingHistorySeriesByCode } from '../api/packaging-cost-types'
import { roleLabel } from './packaging-price'

/** Màu từng đường theo thứ tự (chai → nắp → nhãn → nhãn thùng → thùng); quá năm đường thì quay vòng. */
export const SERIES_COLORS = ['#00AEEF', '#0B6A3A', '#F59E0B', '#8B5CF6', '#EF4444', '#64748B'] as const

export const seriesColor = (index: number): string => SERIES_COLORS[index % SERIES_COLORS.length]

/** Nhãn chú giải: "Chai · CHAI0085". */
export const seriesLabel = (s: Pick<PackagingHistorySeriesByCode, 'code' | 'role'>): string =>
  [roleLabel(s.role), s.code].filter(Boolean).join(' · ')

/** Bỏ đường không có điểm nào, xếp theo thành phần rồi mã — thứ tự (và màu) ổn định giữa các lần nạp. */
export function normalizeSeriesByCode(list: readonly PackagingHistorySeriesByCode[] | null | undefined): PackagingHistorySeriesByCode[] {
  return (list ?? [])
    .filter((s) => s.points.length > 0)
    .map((s) => ({ ...s, points: [...s.points].sort((a, b) => a.date.localeCompare(b.date)) }))
    .sort((a, b) => a.role - b.role || a.code.localeCompare(b.code))
}

/** Các ngày mua (không trùng, cũ → mới) của mọi đường. */
export const collectSeriesDates = (list: readonly PackagingHistorySeriesByCode[]): string[] =>
  [...new Set(list.flatMap((s) => s.points.map((p) => p.date)))].sort()

/** Giá của một đường vào `date` (nhiều lần mua cùng ngày thì lấy lần cuối); không mua ngày đó -> undefined. */
export function priceOnDate(s: PackagingHistorySeriesByCode, date: string): number | undefined {
  let found: number | undefined
  for (const p of s.points) if (p.date === date) found = p.price
  return found
}

/** Đường nối các điểm `(ngày, giá)` đã đổi ra tọa độ; trả chuỗi lệnh path SVG ('' khi không có điểm). */
export function buildSeriesPath(
  s: PackagingHistorySeriesByCode, dates: readonly string[], x: (index: number) => number, y: (price: number) => number,
): string {
  return s.points
    .map((p, k) => `${k === 0 ? 'M' : 'L'}${x(dates.indexOf(p.date)).toFixed(1)},${y(p.price).toFixed(1)}`)
    .join(' ')
}
