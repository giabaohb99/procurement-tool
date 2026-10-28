import type { HeadcountPlanActual, HeadcountPlanPeriod } from '../types/headcount-plan'

/**
 * Câu ghi chú dưới các dòng THỰC TẾ của bảng tự tính (tài liệu 06 §6):
 *
 * - «Thực tế chưa gồm: …» — khoản không có nguồn thực tế (thưởng, phúc lợi…) không nằm trong phần so
 *   được; không nói ra thì người đọc so cả tổng kế hoạch với một con số thực tế thiếu khoản.
 * - «Q3 đang chạy: tính 2 tháng đã qua» — kỳ con chưa hết thì thực tế chỉ có các tháng đã qua, và
 *   «kế hoạch phần so được» cũng chỉ cộng đúng những tháng đó.
 *
 * Mã khoản đổi ra TÊN theo bộ khoản của kế hoạch; mã không còn trong kế hoạch thì giữ nguyên mã.
 */
export function describeActualNotes(
  actual: Pick<HeadcountPlanActual, 'missing_codes' | 'months_counted' | 'limited_scope'>,
  periods: readonly HeadcountPlanPeriod[],
  itemNames: ReadonlyMap<string, string>,
): string[] {
  const notes: string[] = []
  if (actual.limited_scope) {
    notes.push('Không so thực tế: bạn chỉ được xem hợp đồng của một phần nơi này, số thực tế sẽ thiếu.')
  }
  if (actual.missing_codes.length > 0) {
    notes.push(`Thực tế chưa gồm: ${actual.missing_codes.map((c) => itemNames.get(c) || c).join(', ')}.`)
  }
  periods.forEach((p, i) => {
    const counted = actual.months_counted[i]
    if (counted != null && counted > 0 && counted < p.months.length) {
      notes.push(`${p.label} đang chạy: tính ${counted} tháng đã qua.`)
    }
  })
  return notes
}
