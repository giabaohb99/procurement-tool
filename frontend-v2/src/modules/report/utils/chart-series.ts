import type { StatusOption } from '@/shared/constants/statuses'
import type { ChartDatum } from '@/shared/ui/chart'

/**
 * Trải 12 tháng của `year` lên trục T1..T12 và CỘNG các trường số `fields` của
 * từng tháng. Tháng không phát sinh để 0 — thiếu mốc thì trục co lại và người
 * đọc tưởng tháng đó nằm ngoài kỳ. Điểm của năm khác / tháng sai dạng bị bỏ.
 */
export function fillYearMonths<K extends string>(
  year: number,
  rows: ({ month: string } & Partial<Record<K, number>>)[],
  fields: readonly K[],
): ({ label: string } & Record<K, number>)[] {
  const sums = new Map<number, Record<string, number>>()
  for (const row of rows) {
    const [y, m] = row.month.split('-').map(Number)
    if (y !== year || !(m >= 1 && m <= 12)) continue
    const acc = sums.get(m) ?? {}
    for (const f of fields) acc[f] = (acc[f] ?? 0) + Number(row[f] ?? 0)
    sums.set(m, acc)
  }
  return Array.from({ length: 12 }, (_, i) => {
    const acc = sums.get(i + 1) ?? {}
    const point: Record<string, number | string> = { label: `T${i + 1}` }
    for (const f of fields) point[f] = acc[f] ?? 0
    return point as { label: string } & Record<K, number>
  })
}

/**
 * Đếm theo trạng thái, xếp theo VÒNG ĐỜI của bộ mã (`sort_order`, mã ngoại lệ
 * như hủy / tạm ngưng đứng cuối) chứ không theo độ lớn — người đọc dò theo quy
 * trình. Trạng thái 0 dòng bị ẩn; mã lạ backend trả mà bộ mã chưa khai vẫn hiện
 * (nhãn = mã) ở sau cùng, để không dòng nào biến mất khỏi biểu đồ.
 */
export function orderByLifecycle(
  options: readonly StatusOption[],
  counts: { code: string; value: number }[],
): ChartDatum[] {
  const byCode = new Map<string, number>()
  for (const c of counts) byCode.set(c.code, (byCode.get(c.code) ?? 0) + c.value)
  const lifecycle = [
    ...options.filter((s) => !s.is_exception).sort((a, b) => a.sort_order - b.sort_order),
    ...options.filter((s) => s.is_exception),
  ]
  const known = new Set(lifecycle.map((s) => s.value))
  return [
    ...lifecycle
      .filter((s) => (byCode.get(s.value) ?? 0) > 0)
      .map((s) => ({ label: s.label, value: byCode.get(s.value) ?? 0 })),
    ...[...byCode]
      .filter(([code, value]) => !known.has(code) && value > 0)
      .map(([code, value]) => ({ label: code, value })),
  ]
}

/** Lấy `n` hạng mục đầu (backend đã sắp) thành dữ liệu cột ngang, bỏ hạng mục 0. */
export function topBars<T>(
  rows: readonly T[],
  n: number,
  label: (row: T) => string,
  value: (row: T) => number,
): ChartDatum[] {
  return rows
    .map((r) => ({ label: label(r), value: value(r) }))
    .filter((d) => d.value > 0)
    .slice(0, n)
}
