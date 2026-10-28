import { COST_CALC_METHOD_CODE } from '@/shared/constants/statuses'
import type { HeadcountPlanComputedRow } from '../types/headcount-plan'
import type { HrCostItem } from '../types/hr-cost'

const M = COST_CALC_METHOD_CODE

/** Ba dòng tiền của bảng «Tổng» — gom theo CÁCH TÍNH ở giao diện, không theo nhóm chi phí (đã ẩn). */
export type CostBucketKey = 'salary' | 'insurance' | 'bonus'

export const COST_BUCKETS: readonly { key: CostBucketKey; label: string }[] = [
  { key: 'salary', label: 'Lương + phụ cấp' },
  { key: 'insurance', label: 'Bảo hiểm' },
  { key: 'bonus', label: 'Thưởng, quà, chi khác' },
]

/** Tiền / người / tháng → Lương + phụ cấp · % trên lương → Bảo hiểm · còn lại (số tháng lương, theo đợt, cả phòng) → Thưởng. */
export function bucketOfMethod(method: number | undefined): CostBucketKey {
  if (method === M.PER_HEAD_MONTH) return 'salary'
  if (method === M.PERCENT_OF) return 'insurance'
  return 'bonus'
}

export interface CostBucketRow {
  key: CostBucketKey
  label: string
  values: number[]
  total: number
  items: HeadcountPlanComputedRow[]
}

/**
 * Cộng các dòng khoản của bộ tính (`computed.items`) thành 3 dòng. Cách tính của khoản lấy theo MÃ từ bộ
 * khoản trên form; mã lạ (không còn trên form) xếp vào «Thưởng, quà, chi khác» để tổng ba dòng luôn bằng
 * tổng của bộ tính. Dòng không có khoản nào thì bỏ — trừ «Lương + phụ cấp» luôn có.
 */
export function buildCostBucketRows(
  computedItems: readonly HeadcountPlanComputedRow[],
  costItems: readonly Pick<HrCostItem, 'code' | 'calc_method'>[],
  periodCount: number,
): CostBucketRow[] {
  const methodOf = new Map(costItems.map((i) => [i.code, i.calc_method]))
  return COST_BUCKETS.map(({ key, label }) => {
    const items = computedItems.filter((r) => bucketOfMethod(methodOf.get(r.code ?? '')) === key)
    const values = Array.from({ length: periodCount }, (_, i) => items.reduce((acc, r) => acc + (r.values[i] ?? 0), 0))
    const total = items.reduce((acc, r) => acc + (r.total ?? 0), 0)
    return { key, label, values, total, items }
  }).filter((row) => row.key === 'salary' || row.items.length > 0)
}

/** Số người cần có từng kỳ con = cộng mọi dòng (số nguyên không âm), dựng ngay ở giao diện để khỏi chờ bộ tính. */
export function sumLineHeadcounts(lines: readonly { headcounts: readonly number[] }[], periodCount: number): number[] {
  return Array.from({ length: periodCount }, (_, i) =>
    lines.reduce((acc, l) => acc + Math.max(0, Math.trunc(Number(l.headcounts[i]) || 0)), 0),
  )
}
