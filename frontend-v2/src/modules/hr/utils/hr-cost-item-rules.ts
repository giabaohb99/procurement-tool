import {
  COST_ACTUAL_SOURCE_CODE,
  COST_APPLIES_TO_CODE,
  COST_CALC_METHOD_CODE,
} from '@/shared/constants/statuses'
import type { HeadcountPlanLine } from '../types/headcount-plan'
import type { HrCostItem } from '../types/hr-cost'

/**
 * LUẬT của một khoản chi phí (tài liệu 06 §4.2) cho trang Kế hoạch nhân sự.
 *
 * Chỉ là luật HIỂN THỊ + giữ dữ liệu nhất quán khi người dùng sửa (bỏ khoản thì gỡ theo chỗ tham chiếu).
 * Kiểm hợp lệ thật (vòng tham chiếu, tháng ngoài kỳ…) là việc của backend (422) —
 * `hr-cost-item-validation.ts` chỉ báo sớm để người dùng khỏi phải đợi bấm Lưu.
 */

const M = COST_CALC_METHOD_CODE

/** Ô nào có nghĩa với cách tính nào. */
export interface CostItemFieldSpec {
  rate: boolean
  factor: boolean
  cap: boolean
  /** Ô số tiền NGAY TRÊN khoản (khác số tiền nhập theo vị trí ở dòng). */
  amount: boolean
  /** Khoản gốc: `many` cho %, `one` cho số tháng, `null` = không có. */
  baseCodes: 'many' | 'one' | null
  /** Phải chọn ít nhất một tháng rơi vào. */
  monthsRequired: boolean
  /** Số tiền nhập ở từng dòng vị trí (mọc một cột ở khối định biên). */
  perPosition: boolean
  /** Được áp cho «Cả phòng (không theo người)». */
  wholeDepartment: boolean
}

export function describeCostItemFields(method: number): CostItemFieldSpec {
  const none: CostItemFieldSpec = {
    rate: false,
    factor: false,
    cap: false,
    amount: false,
    baseCodes: null,
    monthsRequired: false,
    perPosition: false,
    wholeDepartment: false,
  }
  switch (method) {
    case M.PER_HEAD_MONTH:
      return { ...none, perPosition: true }
    case M.PERCENT_OF:
      return { ...none, rate: true, cap: true, baseCodes: 'many' }
    case M.MONTHS_OF:
      return { ...none, factor: true, baseCodes: 'one', monthsRequired: true }
    case M.PER_HEAD_ONCE:
      return { ...none, amount: true, monthsRequired: true }
    case M.LUMP_SUM:
      return { ...none, amount: true, wholeDepartment: true }
    default:
      return none
  }
}

/** Chuẩn hóa mã khoản: IN HOA, bỏ dấu, ký tự lạ thành `_`, trần 30 ký tự (cột `String(30)`). */
export function normalizeCostCode(raw: string): string {
  return raw
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[đĐ]/g, 'D')
    .toUpperCase()
    .replace(/[^A-Z0-9_]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 30)
}

/** Khoản mới: mã `KHOAN_n` chưa ai dùng, cách tính «theo vị trí», áp cho mọi vị trí. */
export function createEmptyCostItem(existing: readonly HrCostItem[], groupId = 0): HrCostItem {
  const codes = new Set(existing.map((i) => i.code))
  let n = existing.length + 1
  while (codes.has(`KHOAN_${n}`)) n += 1
  const maxOrder = existing.reduce((acc, i) => Math.max(acc, Number(i.sort_order) || 0), 0)
  return {
    code: `KHOAN_${n}`,
    name: '',
    group_id: groupId,
    calc_method: M.PER_HEAD_MONTH,
    rate: null,
    factor: null,
    cap_amount: null,
    amount: null,
    base_codes: [],
    applies_to: COST_APPLIES_TO_CODE.ALL_POSITIONS,
    position_ids: [],
    months: [],
    actual_source: COST_ACTUAL_SOURCE_CODE.NONE,
    sort_order: maxOrder + 10,
  }
}

/** Các khoản «nhập theo vị trí» — mỗi khoản mọc một cột số tiền ở khối định biên. */
export function listPerPositionItems(items: readonly HrCostItem[]): HrCostItem[] {
  return items.filter((i) => describeCostItemFields(i.calc_method).perPosition)
}

/** Khoản có áp cho vị trí này không (cột số tiền của dòng không áp thì khóa lại). */
export function isItemAppliedToPosition(item: HrCostItem, positionId: number): boolean {
  if (item.applies_to !== COST_APPLIES_TO_CODE.SELECTED_POSITIONS) return true
  return item.position_ids.includes(positionId)
}

interface ItemsAndLines {
  items: HrCostItem[]
  lines: HeadcountPlanLine[]
}

/** Bỏ một khoản: gỡ luôn nó khỏi `base_codes` của khoản khác và khỏi số tiền của từng dòng. */
export function removeCostItem(
  items: readonly HrCostItem[],
  lines: readonly HeadcountPlanLine[],
  code: string,
): ItemsAndLines {
  return {
    items: items
      .filter((i) => i.code !== code)
      .map((i) => (i.base_codes.includes(code) ? { ...i, base_codes: i.base_codes.filter((c) => c !== code) } : i)),
    lines: lines.map((l) => {
      if (!l.amounts || !(code in l.amounts)) return l
      const rest = { ...l.amounts }
      delete rest[code]
      return { ...l, amounts: rest }
    }),
  }
}

/**
 * Bỏ mọi khoản người dùng đã TẮT (`excluded`) ở khối «Chi phí khác» — dùng lúc dựng bản xem trước và lúc
 * lưu, nên khoản tắt không vào bảng Tổng và biến khỏi kế hoạch khi bấm Lưu. Gỡ theo cả chỗ tham chiếu
 * (khoản % cũ tính trên khoản vừa tắt), không thì backend 422 «khoản gốc không còn trong kế hoạch».
 */
export function dropExcludedCostItems(
  items: readonly HrCostItem[],
  lines: readonly HeadcountPlanLine[],
): ItemsAndLines {
  return items
    .filter((i) => i.excluded)
    .reduce<ItemsAndLines>((acc, off) => removeCostItem(acc.items, acc.lines, off.code), {
      items: [...items],
      lines: [...lines],
    })
}

/**
 * Xếp khoản theo `sort_order` đã lưu, hai khoản cùng số thì giữ thứ tự đang có — để form thấy đúng thứ
 * tự sẽ lưu.
 */
export function sortCostItemsByOrder(items: readonly HrCostItem[]): HrCostItem[] {
  return items
    .map((item, k) => ({ item, k }))
    .sort((a, b) => (Number(a.item.sort_order) || 0) - (Number(b.item.sort_order) || 0) || a.k - b.k)
    .map(({ item }) => item)
}
