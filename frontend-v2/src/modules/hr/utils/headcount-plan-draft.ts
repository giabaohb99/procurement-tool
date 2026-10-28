import { PLAN_PERIOD_TYPE_CODE } from '@/shared/constants/statuses'
import {
  NO_POSITION_ID,
  WHOLE_COMPANY_DEPARTMENT_ID,
  type HeadcountPlanDetail,
  type HeadcountPlanDocumentLink,
  type HeadcountPlanLine,
  type HeadcountPlanPositionStat,
} from '../types/headcount-plan'
import type { HrCostItem } from '../types/hr-cost'
import { buildSubPeriods, clampPeriodNo, listPeriodMonths, resizeHeadcounts } from './headcount-plan-periods'
import { copyTemplateItemsForPeriod } from './headcount-plan-template-copy'

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
  /** Chỉ dùng lúc TẠO (backend chép khoản từ mẫu); sau đó chỉ để biết đã chép từ đâu. */
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
  /** Tên khoản của mẫu bị bỏ khi chép sang kỳ này (để báo trên form). */
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
    cost_items: (detail.cost_items ?? []).map(normalizeCostItem),
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

/** Chọn mẫu lúc tạo: giữ bộ khoản gốc rồi chép theo kỳ đang chọn. */
export function applyTemplateToDraft(
  draft: HeadcountPlanDraft,
  templateId: number,
  templateItems: readonly HrCostItem[],
): HeadcountPlanDraft {
  const raw = templateItems.map(normalizeCostItem)
  const { items, skipped } = copyTemplateItemsForPeriod(raw, listPeriodMonths(draft.period_type, draft.period_no))
  return {
    ...draft,
    template_id: templateId,
    template_items: raw,
    cost_items: items,
    cost_items_edited: false,
    skipped_items: skipped,
  }
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
  //  Bảng khoản còn nguyên như vừa chép từ mẫu → chép lại theo kỳ mới (Năm có thưởng T12, Q1 thì không).
  //  Người dùng đã sửa tay thì KHÔNG đè — bày cảnh báo «tháng ngoài kỳ» ở từng khoản để họ tự gỡ.
  if (draft.template_items && !draft.cost_items_edited) {
    const { items, skipped } = copyTemplateItemsForPeriod(draft.template_items, listPeriodMonths(periodType, periodNo))
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
 * «ĐANG CÓ» của một dòng. Dòng vị trí thường: đếm đúng vị trí đó. Dòng «Không theo vị trí»: những
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

/** «CẦN TUYỂN» = định biên kỳ con cuối − đang có. Âm nghĩa là đang dư người. */
export function computeNeedToHire(line: HeadcountPlanLine, current: number): number {
  const end = line.headcounts.length ? Number(line.headcounts[line.headcounts.length - 1]) || 0 : 0
  return end - current
}
