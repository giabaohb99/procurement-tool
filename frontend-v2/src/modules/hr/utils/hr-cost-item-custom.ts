import { COST_APPLIES_TO_CODE, COST_CALC_METHOD_CODE } from '@/shared/constants/statuses'
import type { HrCostCustomPart, HrCostItem } from '../types/hr-cost'
import { getCostItemKind, pickDefaultMonthsBase, pickDefaultPercentBases } from './hr-cost-item-kind'

/**
 * LUẬT TỰ ĐẶT của trang kế hoạch (duoc-CR-690): người dùng chỉ khai Tên và một hai con số trong câu ở
 * khối «Chi phí khác»; phần còn lại hệ thống tự đặt:
 * - Khoản % LUÔN tính trên TẤT CẢ khoản «Hằng tháng theo người» (lương + phụ cấp) — tính lại lúc dựng
 *   payload, nên kế hoạch có thêm cột tiền / người vẫn được cộng vào.
 * - «Số tháng lương» tính trên khoản hằng tháng lấy thực tế từ Lương (không có thì khoản hằng tháng đầu).
 * - Áp cho mọi vị trí (khoản cả phòng: cả phòng). Thứ tự = thứ tự trên form.
 *
 * Khoản CŨ có cấu hình mà câu sửa tại chỗ không biểu diễn được thì giữ nguyên phần đó (`custom_parts`) —
 * form chỉ đọc ra câu mô tả kèm nhãn «giữ nguyên».
 */

const M = COST_CALC_METHOD_CODE

const sameSet = (a: readonly string[], b: readonly string[]) =>
  a.length === b.length && a.every((x) => b.includes(x))

/** «Áp cho» của form gọn: khoản cả phòng thì cả phòng, còn lại mọi vị trí. */
const simpleAppliesTo = (method: number) =>
  method === M.LUMP_SUM ? COST_APPLIES_TO_CODE.WHOLE_DEPARTMENT : COST_APPLIES_TO_CODE.ALL_POSITIONS

/** «Tính trên khoản» của form gọn; `null` = cách tính không có khoản gốc. */
function simpleBaseCodes(method: number, others: readonly HrCostItem[]): string[] | null {
  if (method === M.PERCENT_OF) return pickDefaultPercentBases(others)
  if (method === M.MONTHS_OF) return pickDefaultMonthsBase(others)
  return null
}

/**
 * Phần nào của khoản mà câu sửa tại chỗ KHÔNG biểu diễn được. `others` = mọi khoản khác của bộ. Câu chỉ
 * có MỘT ô «chi tháng», nên khoản theo đợt chi nhiều tháng cũng là cấu hình riêng; khoản cả phòng để trống
 * tháng (chia đều mọi tháng) thì câu biểu diễn được («chia đều»).
 */
export function detectCostCustomParts(item: HrCostItem, others: readonly HrCostItem[]): HrCostCustomPart[] {
  const out: HrCostCustomPart[] = []
  if (item.applies_to !== simpleAppliesTo(item.calc_method)) out.push('applies')
  const bases = simpleBaseCodes(item.calc_method, others)
  if (bases && !sameSet(item.base_codes, bases)) out.push('bases')
  const batch = getCostItemKind(item.calc_method) === 'batch'
  if (batch ? item.months.length > 1 : item.months.length > 0) out.push('months')
  return out
}

/** Đánh dấu cấu hình riêng cho cả bộ khoản vừa nạp từ máy chủ (kế hoạch, bản chép từ mẫu gợi ý). */
export function markCostItemsCustomSetup(items: readonly HrCostItem[]): HrCostItem[] {
  return items.map((item, k) => {
    const parts = detectCostCustomParts(item, items.filter((_, j) => j !== k))
    return { ...item, custom_parts: parts.length ? parts : undefined }
  })
}

/** Đặt lại các phần hệ thống tự đặt của MỘT khoản, trừ phần đang giữ làm cấu hình riêng. */
export function applyCostAutoSetup(item: HrCostItem, others: readonly HrCostItem[]): HrCostItem {
  const keep = new Set(item.custom_parts ?? [])
  const next = { ...item }
  if (!keep.has('applies')) {
    next.applies_to = simpleAppliesTo(item.calc_method)
    next.position_ids = []
  }
  const bases = simpleBaseCodes(item.calc_method, others)
  if (!keep.has('bases')) next.base_codes = bases ?? []
  return next
}

/**
 * Bộ khoản đã tự đặt xong — gọi trước khi gửi lên: thứ tự theo vị trí trên form, khoản % / số tháng
 * lương tính lại khoản gốc theo bộ hiện tại.
 */
export function finalizeCostItems(items: readonly HrCostItem[]): HrCostItem[] {
  return items.map((item, k) => ({
    ...applyCostAutoSetup(item, items.filter((_, j) => j !== k)),
    sort_order: (k + 1) * 10,
  }))
}
