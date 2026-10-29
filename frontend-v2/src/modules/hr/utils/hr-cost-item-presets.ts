import { COST_APPLIES_TO_CODE, COST_CALC_METHOD_CODE } from '@/shared/constants/statuses'
import { stripDiacritics } from '@/shared/utils/vn-text'
import type { HrCostGroup, HrCostItem, HrCostTemplate } from '../types/hr-cost'
import { suggestCostCode } from './hr-cost-item-code'
import { applyCostAutoDefaults, pickDefaultMonthsBase, pickDefaultPercentBases } from './hr-cost-item-kind'
import { createEmptyCostItem } from './hr-cost-item-rules'

const M = COST_CALC_METHOD_CODE

/** Mã của hai cột tiền LUÔN có ở bảng «Người và lương» — trùng mã của «Mẫu gợi ý» ở backend. */
export const SALARY_CODE = 'LUONG'
export const ALLOWANCE_CODE = 'PHU_CAP'

/**
 * Trần đóng bảo hiểm điền sẵn cho khoản «Bảo hiểm + công đoàn» — mức 20 × lương cơ sở từ 01/7/2026.
 * Chỉ là số gợi ý: mã không nhớ luật, người dùng tự sửa khi luật đổi (tài liệu 06 §4.2).
 */
export const INSURANCE_CAP_HINT_AMOUNT = 50_600_000

/** Bốn loại của nút «Thêm chi phí» ở khối «Chi phí khác» — mỗi loại một cách tính của backend (2…5). */
export type OtherCostKind = 'percent' | 'months_of' | 'per_head_once' | 'lump_sum'

export const OTHER_COST_KINDS: readonly { kind: OtherCostKind; label: string; hint: string }[] = [
  { kind: 'percent', label: '% trên lương', hint: 'Ví dụ: bảo hiểm công ty đóng 23,5%' },
  { kind: 'months_of', label: 'Số tháng lương', hint: 'Ví dụ: thưởng tháng 13' },
  { kind: 'per_head_once', label: 'Theo đợt mỗi người', hint: 'Ví dụ: quà 8/3, mỗi người 500.000 đ' },
  { kind: 'lump_sum', label: 'Cả phòng', hint: 'Ví dụ: du lịch, liên hoan cả phòng' },
]

interface PresetContext {
  items: readonly HrCostItem[]
  groups: readonly HrCostGroup[]
  /** Tháng của kỳ kế hoạch; vắng = cả 12 tháng. */
  periodMonths?: readonly number[]
}

/** Tháng 12 nếu kỳ có; kỳ không chứa T12 thì tháng cuối của kỳ — để khoản mới không rơi ngoài kỳ. */
function pickYearEndMonth(periodMonths: readonly number[] | undefined): number {
  if (!periodMonths?.length || periodMonths.includes(12)) return 12
  return Math.max(...periodMonths)
}

/** Dựng khoản MỚI: nhóm + nguồn thực tế tự đặt, mã tự sinh từ tên (hoặc mã cho sẵn), không trùng khoản đã có. */
function buildItem(name: string, over: Partial<HrCostItem>, { items, groups }: PresetContext, code?: string): HrCostItem {
  const item = applyCostAutoDefaults({ ...createEmptyCostItem(items, groups[0]?.id ?? 0), name, ...over }, groups)
  return { ...item, code: code ?? suggestCostCode(name, items.map((i) => i.code)) }
}

function buildInsurance(ctx: PresetContext): HrCostItem {
  return buildItem(
    'Bảo hiểm + công đoàn',
    { calc_method: M.PERCENT_OF, rate: 23.5, cap_amount: INSURANCE_CAP_HINT_AMOUNT, base_codes: pickDefaultPercentBases(ctx.items) },
    ctx,
  )
}

function buildBonus13(ctx: PresetContext): HrCostItem {
  return buildItem(
    'Thưởng tháng 13',
    { calc_method: M.MONTHS_OF, factor: 1, base_codes: pickDefaultMonthsBase(ctx.items), months: [pickYearEndMonth(ctx.periodMonths)] },
    ctx,
  )
}

/**
 * Dòng MỚI của nút «Thêm chi phí», điền sẵn tên gợi ý. Chỉ điền số khi con số là chuẩn chung (bảo hiểm
 * 23,5%, thưởng 1 tháng lương); số tiền quà / chi cả phòng để trống cho người dùng tự nhập.
 */
export function buildOtherCostItem(kind: OtherCostKind, ctx: PresetContext): HrCostItem {
  switch (kind) {
    case 'percent':
      //  Đã có bảo hiểm thì khoản % thứ hai là thứ khác (công đoàn riêng, quỹ…) — không chép lại 23,5%.
      return ctx.items.some((i) => i.calc_method === M.PERCENT_OF)
        ? buildItem('Chi phí theo % lương', { calc_method: M.PERCENT_OF, base_codes: pickDefaultPercentBases(ctx.items) }, ctx)
        : buildInsurance(ctx)
    case 'months_of':
      return buildBonus13(ctx)
    case 'per_head_once':
      return buildItem('Quà theo đợt', { calc_method: M.PER_HEAD_ONCE, months: [ctx.periodMonths?.[0] ?? 1] }, ctx)
    case 'lump_sum':
      return buildItem('Chi chung cả phòng', { calc_method: M.LUMP_SUM, applies_to: COST_APPLIES_TO_CODE.WHOLE_DEPARTMENT }, ctx)
  }
}

/**
 * Bảo đảm bộ khoản có LƯƠNG và PHỤ CẤP (hai cột tiền của bảng «Người và lương») — thiếu Lương thì thêm vào
 * ĐẦU bộ, thiếu Phụ cấp thì thêm ngay sau Lương (cột luôn đọc «Lương/người · Phụ cấp/người»). `added` = có
 * thêm, để nơi gọi biết bộ khoản đã khác mẫu gợi ý.
 */
export function ensureSalaryItems(
  items: readonly HrCostItem[],
  groups: readonly HrCostGroup[],
): { items: HrCostItem[]; added: boolean } {
  let out = [...items]
  const has = (code: string) => out.some((i) => i.code === code)
  const monthly = (name: string, code: string) =>
    buildItem(name, { calc_method: M.PER_HEAD_MONTH }, { items: out, groups }, code)
  const added = !has(SALARY_CODE) || !has(ALLOWANCE_CODE)
  if (!has(SALARY_CODE)) out = [monthly('Lương', SALARY_CODE), ...out]
  if (!has(ALLOWANCE_CODE)) {
    const at = out.findIndex((i) => i.code === SALARY_CODE)
    out = [...out.slice(0, at + 1), monthly('Phụ cấp', ALLOWANCE_CODE), ...out.slice(at + 1)]
  }
  //  Đánh lại thứ tự theo vị trí: bộ khoản được xếp theo `sort_order` khi nạp vào form.
  return { items: added ? out.map((i, k) => ({ ...i, sort_order: (k + 1) * 10 })) : out, added }
}

/**
 * Bộ khoản DỰNG Ở GIAO DIỆN khi máy chủ không có mẫu nào đang dùng: Lương · Phụ cấp · Bảo hiểm 23,5% ·
 * Thưởng tháng 13 — đúng bộ «Mẫu gợi ý» của backend.
 */
export function buildSuggestedCostItems(groups: readonly HrCostGroup[], periodMonths?: readonly number[]): HrCostItem[] {
  const base = ensureSalaryItems([], groups).items
  const insurance = buildInsurance({ items: base, groups, periodMonths })
  const withInsurance = [...base, insurance]
  return [...withInsurance, buildBonus13({ items: withInsurance, groups, periodMonths })]
}

/** Tên mẫu backend tạo sẵn (`legacy_seed.SUGGESTED_TEMPLATE`). */
export const SUGGESTED_TEMPLATE_NAME = 'Mẫu gợi ý'

/**
 * Mẫu dùng để ĐIỀN SẴN chi phí cho kế hoạch mới: mẫu đang dùng tên «Mẫu gợi ý» (không phân biệt dấu / hoa
 * thường), không có thì mẫu đang dùng đầu tiên; `0` = không có mẫu nào (giao diện tự dựng bộ gợi ý).
 */
export function pickSuggestedTemplateId(templates: readonly Pick<HrCostTemplate, 'id' | 'name' | 'is_active'>[]): number {
  const active = templates.filter((t) => t.is_active)
  const wanted = stripDiacritics(SUGGESTED_TEMPLATE_NAME)
  return (active.find((t) => stripDiacritics(t.name).trim() === wanted) ?? active[0])?.id ?? 0
}

/**
 * Tiêu đề cột tiền của bảng «Người và lương»: «Lương/người», «Phụ cấp/người»; khoản hằng tháng khác (dữ
 * liệu cũ) lấy theo tên của nó.
 */
export function describePerHeadColumn(item: Pick<HrCostItem, 'code' | 'name'>): string {
  if (item.code === SALARY_CODE) return 'Lương/người'
  if (item.code === ALLOWANCE_CODE) return 'Phụ cấp/người'
  return `${item.name.trim() || item.code}/người`
}
