import type { SpendPoint } from '@/modules/procurement/types/purchase-report'

/** Một mốc tháng trên biểu đồ so sánh hai năm. */
export interface MonthComparisonPoint {
  /** "T1".."T12". */
  label: string
  current: number
  /** Cùng tháng của năm trước. */
  previous: number
}

/**
 * Trải 12 tháng của năm `year` và năm trước lên cùng một trục T1..T12.
 *
 * Tháng không phát sinh vẫn giữ mốc với giá trị 0 — thiếu mốc thì đường gấp
 * khúc nối thẳng qua tháng trống và người đọc tưởng tháng đó có số.
 * Điểm của NĂM KHÁC lẫn vào (backend lọc theo `period`, không theo chuỗi
 * tháng) bị bỏ qua chứ không cộng dồn nhầm năm.
 */
export function buildMonthComparison(
  year: number,
  current: SpendPoint[],
  previous: SpendPoint[],
): MonthComparisonPoint[] {
  const byMonth = (points: SpendPoint[], y: number) => {
    const map = new Map<number, number>()
    for (const point of points) {
      const [py, pm] = point.month.split('-').map(Number)
      if (py !== y || !(pm >= 1 && pm <= 12)) continue
      map.set(pm, (map.get(pm) ?? 0) + Number(point.amount || 0))
    }
    return map
  }
  const cur = byMonth(current, year)
  const prev = byMonth(previous, year - 1)
  return Array.from({ length: 12 }, (_, i) => ({
    label: `T${i + 1}`,
    current: cur.get(i + 1) ?? 0,
    previous: prev.get(i + 1) ?? 0,
  }))
}

/**
 * Số tháng được đem so của năm đang xem: năm đã qua = cả 12 tháng; năm hiện
 * tại = tới hết tháng hiện tại (so CÙNG KỲ, như Haravan). Lấy cả năm trước so
 * với 9 tháng năm nay thì năm nào cũng "giảm" — con số sai mà trông hợp lý.
 * Năm tương lai = 0 (chưa có kỳ nào để so).
 */
export function comparableMonthCount(year: number, today: Date): number {
  const thisYear = today.getFullYear()
  if (year < thisYear) return 12
  if (year > thisYear) return 0
  return today.getMonth() + 1
}

/**
 * Điểm để VẼ: tháng chưa tới của năm đang xem thành `null` để đường kỳ này dừng
 * ở tháng hiện tại. Để 0 thì đường cắm đầu xuống đáy ở tháng 10 và người đọc
 * tưởng chi tiêu sụp đổ.
 */
export function maskFutureMonths(points: MonthComparisonPoint[], months: number) {
  return points.map((p, i) => ({ ...p, current: i < months ? p.current : null }))
}

/** Tổng `current` / `previous` của `months` tháng đầu năm. */
export function sumFirstMonths(points: MonthComparisonPoint[], months: number) {
  return points.slice(0, Math.max(0, months)).reduce(
    (acc, p) => ({ current: acc.current + p.current, previous: acc.previous + p.previous }),
    { current: 0, previous: 0 },
  )
}

/**
 * Phần trăm thay đổi so với kỳ trước. `null` khi kỳ trước bằng 0 (hoặc không
 * phải số): "tăng vô hạn %" không nói được gì, màn hình ghi "Chưa có kỳ trước".
 */
export function percentChange(current: number, previous: number): number | null {
  if (!Number.isFinite(current) || !Number.isFinite(previous) || previous === 0) return null
  return ((current - previous) / Math.abs(previous)) * 100
}

/** Tỷ lệ phần trăm an toàn: mẫu 0 thì `null` (chưa có giao hàng nào để đo). */
export function ratePercent(part: number, total: number): number | null {
  if (!Number.isFinite(part) || !Number.isFinite(total) || total <= 0) return null
  return (part / total) * 100
}
