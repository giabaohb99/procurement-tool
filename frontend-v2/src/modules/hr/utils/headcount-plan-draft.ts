import { PLAN_PERIOD_TYPE_CODE } from '@/shared/constants/statuses'
import {
  NO_POSITION_ID,
  WHOLE_COMPANY_DEPARTMENT_ID,
  type HeadcountPlanDetail,
  type HeadcountPlanDocumentLink,
  type HeadcountPlanLine,
  type HeadcountPlanPositionStat,
} from '../types/headcount-plan'
import type { HrCostGroup, HrCostItem } from '../types/hr-cost'
import { buildSubPeriods, clampPeriodNo, listPeriodMonths, resizeHeadcounts } from './headcount-plan-periods'
import { copyTemplateItemsForPeriod } from './headcount-plan-template-copy'
import { markCostItemsCustomSetup } from './hr-cost-item-custom'
import { ensureSalaryItems } from './hr-cost-item-presets'
import { sortCostItemsByOrder } from './hr-cost-item-rules'

/**
 * BẢN NHÁP của trang kế hoạch nhân sự — một object duy nhất giữ cả bốn khối, cùng khuôn với các
 * trang chứng từ dài (Đặt phòng họp, YCMH): `useState` + hàm thuần, không react-hook-form, vì bảng
 * khoản và bảng dòng có CỘT ĐỘNG theo mã khoản (khóa `amounts[code]`) mà field array không biểu
 * diễn gọn được.
 */
export interface HeadcountPlanDraft {
  year: number
  period_type: number
  period_no: number
  company_id: number
  department_id: number
  /**
   * Mẫu gợi ý đã điền sẵn chi phí lúc TẠO (tự chọn, người dùng không thấy). `0` = bộ khoản dựng ở giao
   * diện hoặc đã khác mẫu (thêm Lương / Phụ cấp) → lúc tạo phải gửi `cost_items` lên.
   */
  template_id: number
  basis_no: string
  /** `YYYY-MM-DD`, chuỗi rỗng = chưa nhập. */
  basis_date: string
  approver_employee_id: number
  note: string
  cost_items: HrCostItem[]
  lines: HeadcountPlanLine[]
  documents: HeadcountPlanDocumentLink[]
  /**
   * Bộ khoản GỐC của mẫu đã chọn (chỉ lúc TẠO). Còn giữ nó thì đổi kỳ là chép lại từ mẫu theo kỳ mới —
   * cùng luật bỏ khoản rơi ngoài kỳ như backend — cho tới khi người dùng tự sửa bảng khoản.
   */
  template_items: HrCostItem[] | null
  /** Người dùng đã sửa bảng khoản sau khi chép từ mẫu → lúc tạo phải gửi `cost_items` lên. */
  cost_items_edited: boolean
  /** Tên chi phí của mẫu gợi ý bị bỏ vì tháng chi nằm ngoài kỳ (để báo trên form). */
  skipped_items: string[]
}

export function createEmptyDraft(year: number): HeadcountPlanDraft {
  return {
    year,
    period_type: PLAN_PERIOD_TYPE_CODE.YEAR,
    period_no: 1,
    company_id: 0,
    department_id: WHOLE_COMPANY_DEPARTMENT_ID,
    template_id: 0,
    basis_no: '',
    basis_date: '',
    approver_employee_id: 0,
    note: '',
    cost_items: [],
    lines: [],
    documents: [],
    template_items: null,
    cost_items_edited: false,
    skipped_items: [],
  }
}

const toNum = (v: unknown): number | null => {
  if (v === null || v === undefined || v === '') return null
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}

/** Khoản từ API → khoản của bản nháp. `rate` / `factor` có thể về dạng chuỗi (Numeric) nên ép số. */
export function normalizeCostItem(raw: HrCostItem): HrCostItem {
  return {
    ...raw,
    rate: toNum(raw.rate),
    factor: toNum(raw.factor),
    cap_amount: toNum(raw.cap_amount),
    amount: toNum(raw.amount),
    base_codes: raw.base_codes ?? [],
    position_ids: raw.position_ids ?? [],
    months: raw.months ?? [],
    group_id: Number(raw.group_id) || 0,
    sort_order: Number(raw.sort_order) || 0,
  }
}

/**
 * Bộ khoản từ API → bộ khoản của bản nháp: chuẩn hóa từng khoản, xếp theo thứ tự đã lưu (danh sách không
 * còn ô «Thứ tự» — vị trí trên danh sách LÀ thứ tự), rồi đánh dấu khoản cũ có cấu hình riêng.
 */
export function normalizeCostItems(raw: readonly HrCostItem[] | null | undefined): HrCostItem[] {
  return markCostItemsCustomSetup(sortCostItemsByOrder((raw ?? []).map(normalizeCostItem)))
}

/** Chép khoản của mẫu theo kỳ, rồi dò lại cấu hình riêng trên bộ đã chép. */
function copyTemplateForPeriod(templateItems: readonly HrCostItem[], periodMonths: readonly number[]) {
  const { items, skipped } = copyTemplateItemsForPeriod(templateItems, periodMonths)
  return { items: markCostItemsCustomSetup(items), skipped }
}

export function draftFromDetail(detail: HeadcountPlanDetail): HeadcountPlanDraft {
  const periods = buildSubPeriods(detail.period_type, detail.period_no).length
  return {
    year: detail.year,
    period_type: detail.period_type,
    period_no: detail.period_no,
    company_id: detail.company_id,
    department_id: detail.department_id,
    template_id: detail.template_id ?? 0,
    basis_no: detail.basis_no ?? '',
    basis_date: detail.basis_date ?? '',
    approver_employee_id: detail.approver_employee_id ?? 0,
    note: detail.note ?? '',
    cost_items: normalizeCostItems(detail.cost_items),
    lines: (detail.lines ?? []).map((l) => ({
      ...l,
      headcounts: resizeHeadcounts(l.headcounts ?? [], periods),
      amounts: l.amounts ?? {},
      note: l.note ?? '',
    })),
    documents: detail.documents ?? [],
    template_items: null,
    cost_items_edited: false,
    skipped_items: [],
  }
}

/** Chép khoản của mẫu lúc tạo: giữ bộ khoản gốc rồi chép theo kỳ đang chọn. */
export function applyTemplateToDraft(
  draft: HeadcountPlanDraft,
  templateId: number,
  templateItems: readonly HrCostItem[],
): HeadcountPlanDraft {
  const raw = normalizeCostItems(templateItems)
  const { items, skipped } = copyTemplateForPeriod(raw, listPeriodMonths(draft.period_type, draft.period_no))
  return {
    ...draft,
    template_id: templateId,
    template_items: raw,
    cost_items: items,
    cost_items_edited: false,
    skipped_items: skipped,
  }
}

/** Bộ chi phí điền sẵn cho kế hoạch MỚI: khoản của «Mẫu gợi ý» (`templateId > 0`) hoặc bộ dựng ở giao diện (`0`). */
export interface HeadcountPlanSeed {
  /** Khóa để chỉ áp MỘT lần cho mỗi nguồn (mẫu nào / bộ giao diện). */
  key: string
  templateId: number
  items: readonly HrCostItem[]
}

/**
 * Điền sẵn chi phí cho kế hoạch mới (không còn ô chọn mẫu): chép khoản của nguồn theo kỳ đang chọn, bảo
 * đảm có Lương + Phụ cấp. Bộ đã khác mẫu (thêm Lương / Phụ cấp, hoặc không có mẫu) thì `template_id = 0`
 * để lúc tạo gửi nguyên bộ lên — backend tự chép mẫu thì mất phần vừa thêm.
 */
export function applySeedToDraft(
  draft: HeadcountPlanDraft,
  seed: HeadcountPlanSeed,
  groups: readonly HrCostGroup[],
): HeadcountPlanDraft {
  const { items, added } = ensureSalaryItems(seed.items, groups)
  const next = applyTemplateToDraft(draft, seed.templateId, items)
  return added || !seed.templateId ? { ...next, template_id: 0 } : next
}

/** «Giống nhau cả năm»: mọi kỳ con của dòng nhận cùng một số người (số nguyên không âm). */
export function fillLineHeadcounts(line: HeadcountPlanLine, value: number): HeadcountPlanLine {
  const n = Math.max(0, Math.trunc(Number(value) || 0))
  return { ...line, headcounts: line.headcounts.map(() => n) }
}

/**
 * Đổi loại kỳ / kỳ: kẹp `period_no` về dải của loại mới và đổi độ dài mảng định biên của MỌI dòng
 * theo số kỳ con mới — không thì backend 422 «độ dài headcounts sai».
 */
export function changeDraftPeriod(
  draft: HeadcountPlanDraft,
  change: { period_type?: number; period_no?: number },
): HeadcountPlanDraft {
  const periodType = change.period_type ?? draft.period_type
  const periodNo = clampPeriodNo(periodType, change.period_no ?? draft.period_no)
  const length = buildSubPeriods(periodType, periodNo).length
  const next: HeadcountPlanDraft = {
    ...draft,
    period_type: periodType,
    period_no: periodNo,
    lines: draft.lines.map((l) => ({ ...l, headcounts: resizeHeadcounts(l.headcounts, length) })),
  }
  //  Chi phí còn nguyên như vừa điền sẵn → chép lại theo kỳ mới (Năm có thưởng T12, Q1 thì không).
  //  Người dùng đã sửa tay thì KHÔNG đè — bày cảnh báo «tháng ngoài kỳ» ở từng dòng để họ tự sửa.
  if (draft.template_items && !draft.cost_items_edited) {
    const { items, skipped } = copyTemplateForPeriod(draft.template_items, listPeriodMonths(periodType, periodNo))
    return { ...next, cost_items: items, skipped_items: skipped }
  }
  return next
}

/** Thêm dòng vị trí. Vị trí đã có dòng thì giữ nguyên (backend UNIQUE plan × vị trí). */
export function addDraftLine(draft: HeadcountPlanDraft, positionId: number, positionName: string): HeadcountPlanDraft {
  if (draft.lines.some((l) => l.position_id === positionId)) return draft
  const length = buildSubPeriods(draft.period_type, draft.period_no).length
  const line: HeadcountPlanLine = {
    position_id: positionId,
    position_name: positionName,
    headcounts: Array.from({ length }, () => 0),
    amounts: {},
    note: '',
  }
  return { ...draft, lines: [...draft.lines, line] }
}

/**
 * «HIỆN CÓ» của một dòng. Dòng vị trí thường: đếm đúng vị trí đó. Dòng «Cả phòng (không chia vị trí)»: những
 * người của pháp nhân × phòng KHÔNG thuộc vị trí nào đã có dòng riêng — cộng cả bảng thì người của
 * «Kế toán viên» bị đếm hai lần khi kế hoạch có cả dòng vị trí lẫn dòng tổng.
 */
export function countCurrentForLine(
  line: HeadcountPlanLine,
  lines: readonly HeadcountPlanLine[],
  stats: readonly HeadcountPlanPositionStat[],
): number {
  if (line.position_id !== NO_POSITION_ID) {
    return stats.find((s) => s.position_id === line.position_id)?.current_count ?? 0
  }
  const listed = new Set(lines.filter((l) => l.position_id !== NO_POSITION_ID).map((l) => l.position_id))
  return stats.filter((s) => !listed.has(s.position_id)).reduce((acc, s) => acc + (s.current_count || 0), 0)
}

/** «CẦN TUYỂN» = số người cần có ở kỳ con cuối − hiện có. Âm nghĩa là đang dư người. */
export function computeNeedToHire(line: HeadcountPlanLine, current: number): number {
  const end = line.headcounts.length ? Number(line.headcounts[line.headcounts.length - 1]) || 0 : 0
  return end - current
}
