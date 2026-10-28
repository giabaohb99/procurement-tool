import {
  COST_ACTUAL_SOURCE_CODE,
  COST_APPLIES_TO_CODE,
  COST_CALC_METHOD_CODE,
} from '@/shared/constants/statuses'
import type { HeadcountPlanLine } from '../types/headcount-plan'
import type { HrCostItem } from '../types/hr-cost'

/**
 * LUẬT của một khoản chi phí (tài liệu 06 §4.2) dùng chung cho bảng khoản ở màn Mẫu và màn Kế hoạch.
 *
 * Chỉ là luật HIỂN THỊ + giữ dữ liệu nhất quán khi người dùng sửa (bỏ ô thừa khi đổi cách tính, đổi
 * tên mã thì đổi theo chỗ tham chiếu). Kiểm hợp lệ thật (vòng tham chiếu, tháng ngoài kỳ…) là việc của
 * backend (422) — `listCostItemProblems` chỉ báo sớm để người dùng khỏi phải đợi bấm Lưu.
 */

const M = COST_CALC_METHOD_CODE

/**
 * Nguồn thực tế (`COST_ACTUAL_SOURCE_CODE`) dùng được với cách tính nào — khớp backend `costing._check_actual_source`:
 * lương cơ bản / phụ cấp chỉ cho «số tiền / người / tháng»; % × lương đóng BHXH chỉ cho khoản «%».
 */
export function listActualSourcesFor(method: number): number[] {
  const S = COST_ACTUAL_SOURCE_CODE
  if (method === M.PER_HEAD_MONTH) return [S.NONE, S.BASE_SALARY, S.ALLOWANCE]
  if (method === M.PERCENT_OF) return [S.NONE, S.PERCENT_OF_INSURANCE_SALARY]
  return [S.NONE]
}

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

/**
 * Đổi cách tính: bỏ giá trị của các ô không còn nghĩa (để khỏi gửi lên một tỷ lệ «ma» cho khoản tiền
 * cả phòng), và kéo «Cả phòng» về «Mọi vị trí» khi cách tính mới không cho áp cả phòng.
 */
export function changeCostItemMethod(item: HrCostItem, method: number): HrCostItem {
  const spec = describeCostItemFields(method)
  const baseCodes = spec.baseCodes === 'one' ? item.base_codes.slice(0, 1) : spec.baseCodes ? item.base_codes : []
  return {
    ...item,
    calc_method: method,
    rate: spec.rate ? item.rate : null,
    factor: spec.factor ? (item.factor ?? 1) : null,
    cap_amount: spec.cap ? item.cap_amount : null,
    amount: spec.amount ? item.amount : null,
    base_codes: baseCodes,
    // Đổi cách tính làm nguồn thực tế cũ hết hợp lệ thì bỏ về «không có nguồn» (backend sẽ 422 nếu để lại)
    actual_source: listActualSourcesFor(method).includes(item.actual_source) ? item.actual_source : COST_ACTUAL_SOURCE_CODE.NONE,
    applies_to:
      !spec.wholeDepartment && item.applies_to === COST_APPLIES_TO_CODE.WHOLE_DEPARTMENT
        ? COST_APPLIES_TO_CODE.ALL_POSITIONS
        : item.applies_to,
  }
}

/**
 * Khoản nào được làm KHOẢN GỐC cho `item`. % chỉ trỏ tới khoản cách tính 1 hoặc 3; số tháng chỉ trỏ
 * khoản cách tính 1 — để không có vòng lặp tham chiếu (§4.2). Không bao giờ tự trỏ chính mình.
 */
export function listBaseCandidates(items: readonly HrCostItem[], item: HrCostItem): HrCostItem[] {
  const spec = describeCostItemFields(item.calc_method)
  if (!spec.baseCodes) return []
  const allowed: number[] = spec.baseCodes === 'many' ? [M.PER_HEAD_MONTH, M.MONTHS_OF] : [M.PER_HEAD_MONTH]
  return items.filter((i) => i.code && i.code !== item.code && allowed.includes(i.calc_method))
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

/**
 * Đổi MÃ một khoản. Mã là khóa tham chiếu, nên đổi theo cả `base_codes` của các khoản khác lẫn khóa
 * `amounts` của từng dòng — không thì khoản % mất khoản gốc và số tiền đã nhập rơi mất, im lặng.
 * Mã mới trùng một khoản KHÁC thì không đổi gì (đổi vào là hai khoản dính nhau).
 */
export function renameCostItemCode(
  items: readonly HrCostItem[],
  lines: readonly HeadcountPlanLine[],
  oldCode: string,
  rawNewCode: string,
): ItemsAndLines {
  const newCode = normalizeCostCode(rawNewCode)
  const unchanged = { items: [...items], lines: [...lines] }
  if (!newCode || newCode === oldCode) return unchanged
  if (items.some((i) => i.code === newCode)) return unchanged
  return {
    items: items.map((i) => ({
      ...i,
      code: i.code === oldCode ? newCode : i.code,
      base_codes: i.base_codes.map((c) => (c === oldCode ? newCode : c)),
    })),
    lines: lines.map((l) => {
      if (!l.amounts || !(oldCode in l.amounts)) return l
      const { [oldCode]: moved, ...rest } = l.amounts
      return { ...l, amounts: { ...rest, [newCode]: moved } }
    }),
  }
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

/** Đổi chỗ khoản lên / xuống rồi đánh lại `sort_order` 10·20·30… để thứ tự lưu đúng thứ tự thấy. */
export function moveCostItem(items: readonly HrCostItem[], index: number, delta: -1 | 1): HrCostItem[] {
  const target = index + delta
  if (index < 0 || index >= items.length || target < 0 || target >= items.length) return [...items]
  const next = [...items]
  ;[next[index], next[target]] = [next[target], next[index]]
  return next.map((i, k) => ({ ...i, sort_order: (k + 1) * 10 }))
}

/**
 * Báo sớm các chỗ backend sẽ chặn (422), theo từng khoản. `periodMonths` rỗng = màn Mẫu (chưa có kỳ,
 * không kiểm tháng ngoài kỳ).
 */
export function listCostItemProblems(
  item: HrCostItem,
  items: readonly HrCostItem[],
  periodMonths: readonly number[] = [],
): string[] {
  const out: string[] = []
  const spec = describeCostItemFields(item.calc_method)
  if (!item.code) out.push('Chưa có mã khoản.')
  else if (items.filter((i) => i.code === item.code).length > 1) out.push(`Mã «${item.code}» bị trùng.`)
  if (!item.name.trim()) out.push('Chưa đặt tên khoản.')
  if (spec.baseCodes) {
    const known = new Set(listBaseCandidates(items, item).map((i) => i.code))
    if (item.base_codes.length === 0) out.push('Chưa chọn khoản gốc.')
    else if (item.base_codes.some((c) => !known.has(c))) out.push('Khoản gốc không hợp lệ (đã bỏ hoặc sai cách tính).')
  }
  if (spec.monthsRequired && item.months.length === 0) out.push('Chưa chọn tháng rơi vào.')
  if (!listActualSourcesFor(item.calc_method).includes(item.actual_source)) {
    out.push('Nguồn thực tế không dùng được với cách tính này.')
  }
  if (periodMonths.length && item.months.some((m) => !periodMonths.includes(m))) {
    out.push('Có tháng rơi vào nằm ngoài kỳ của kế hoạch.')
  }
  if (item.applies_to === COST_APPLIES_TO_CODE.SELECTED_POSITIONS && item.position_ids.length === 0) {
    out.push('Chọn «Các vị trí đã chọn» nhưng chưa chọn vị trí nào.')
  }
  return out
}
