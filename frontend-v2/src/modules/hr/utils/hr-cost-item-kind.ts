import { COST_ACTUAL_SOURCE_CODE, COST_CALC_METHOD_CODE } from '@/shared/constants/statuses'
import type { HrCostGroup, HrCostItem } from '../types/hr-cost'

/**
 * Ba NHÓM nghĩa đặt trên 5 cách tính của backend (tài liệu 06 §4.2): hằng tháng theo người (1), phần
 * trăm trên lương (2), theo đợt (3 số tháng lương · 4 mỗi người · 5 cả phòng).
 */
export type CostItemKind = 'monthly' | 'percent' | 'batch'

const M = COST_CALC_METHOD_CODE

export function getCostItemKind(method: number): CostItemKind {
  if (method === M.PER_HEAD_MONTH) return 'monthly'
  if (method === M.PERCENT_OF) return 'percent'
  return 'batch'
}

/** Mặc định «Tính trên khoản» của khoản %: MỌI khoản «Hằng tháng theo người» khác. */
export function pickDefaultPercentBases(others: readonly HrCostItem[]): string[] {
  return others.filter((i) => i.code && i.calc_method === M.PER_HEAD_MONTH).map((i) => i.code)
}

/** Mặc định gốc của «số tháng lương»: khoản lấy thực tế từ lương HĐ, không có thì khoản hằng tháng đầu tiên. */
export function pickDefaultMonthsBase(others: readonly HrCostItem[]): string[] {
  const monthly = others.filter((i) => i.code && i.calc_method === M.PER_HEAD_MONTH)
  const salary = monthly.find((i) => i.actual_source === COST_ACTUAL_SOURCE_CODE.BASE_SALARY) ?? monthly[0]
  return salary ? [salary.code] : []
}

/** Bỏ dấu + chữ thường, để so tên nhóm / dò chữ «lương» trong tên khoản. */
function foldText(s: string): string {
  return s
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[đĐ]/g, 'd')
    .toLowerCase()
    .trim()
}

/** Tên nhóm tự chọn theo cách tính (đúng tên trong danh mục gợi ý của tài liệu 06 §4.1). */
export function pickAutoGroupName(method: number): string {
  if (method === M.PER_HEAD_MONTH || method === M.MONTHS_OF) return 'Quỹ lương'
  if (method === M.PERCENT_OF) return 'Bắt buộc theo luật'
  return 'Phúc lợi'
}

/** Nhóm có tên khớp (không phân biệt dấu / hoa thường, ưu tiên nhóm đang dùng); không có thì nhóm đầu tiên. */
export function findCostGroupId(groups: readonly HrCostGroup[], name: string): number {
  const wanted = foldText(name)
  const sorted = [...groups].sort((a, b) => Number(b.is_active) - Number(a.is_active))
  return (sorted.find((g) => foldText(g.name) === wanted) ?? sorted[0])?.id ?? 0
}

/** «Lấy số thực tế» tự chọn: khoản % → % × lương đóng BHXH; khoản hằng tháng dò chữ «phụ cấp» / «lương» trong tên. */
export function pickAutoActualSource(item: Pick<HrCostItem, 'name' | 'calc_method'>): number {
  const S = COST_ACTUAL_SOURCE_CODE
  if (item.calc_method === M.PERCENT_OF) return S.PERCENT_OF_INSURANCE_SALARY
  if (item.calc_method !== M.PER_HEAD_MONTH) return S.NONE
  const name = foldText(item.name)
  if (name.includes('phu cap')) return S.ALLOWANCE
  if (/\bluong\b/.test(name)) return S.BASE_SALARY
  return S.NONE
}

/**
 * Nhóm và «Lấy số thực tế» TỰ ĐẶT theo cách tính (và theo tên, với khoản hằng tháng). Trang kế hoạch không có
 * ô nào cho hai thứ này; danh mục nhóm rỗng thì giữ nhóm đang có thay vì về 0.
 */
export function applyCostAutoDefaults(item: HrCostItem, groups: readonly HrCostGroup[]): HrCostItem {
  return {
    ...item,
    group_id: findCostGroupId(groups, pickAutoGroupName(item.calc_method)) || item.group_id,
    actual_source: pickAutoActualSource(item),
  }
}
