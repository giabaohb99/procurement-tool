import { PLAN_PERIOD_TYPE_CODE } from '@/shared/constants/statuses'
import type { HeadcountPlanPeriod } from '../types/headcount-plan'

/**
 * KỲ và KỲ CON của kế hoạch nhân sự (tài liệu 06 §3). Bản này chỉ để DỰNG CỘT trước khi bộ tính ở
 * backend trả lời (số cột định biên phải có ngay khi người dùng đổi loại kỳ) — nguồn con số vẫn là
 * `costing.compute_plan`, và khóa / tháng của kỳ con phải khớp `periods` mà backend trả.
 *
 * | Loại kỳ  | Kỳ con                 | period_no |
 * |----------|------------------------|-----------|
 * | Năm      | Q1 · Q2 · Q3 · Q4      | 1         |
 * | Bán niên | 2 quý của nửa năm đó   | 1–2       |
 * | Quý      | 3 tháng của quý        | 1–4       |
 * | Tháng    | một cột                | 1–12      |
 */

const range = (from: number, to: number) => Array.from({ length: to - from + 1 }, (_, i) => from + i)

const quarter = (q: number): HeadcountPlanPeriod => ({
  key: `Q${q}`,
  label: `Q${q}`,
  months: range(q * 3 - 2, q * 3),
})

const month = (m: number): HeadcountPlanPeriod => ({ key: `M${m}`, label: `T${m}`, months: [m] })

/** Số kỳ của một loại kỳ trong năm (giá trị tối đa của `period_no`). Loại lạ → 1. */
export function countPeriodsInYear(periodType: number): number {
  switch (periodType) {
    case PLAN_PERIOD_TYPE_CODE.HALF:
      return 2
    case PLAN_PERIOD_TYPE_CODE.QUARTER:
      return 4
    case PLAN_PERIOD_TYPE_CODE.MONTH:
      return 12
    default:
      return 1
  }
}

/** Ép `period_no` về dải hợp lệ của loại kỳ — đổi Tháng (7) sang Quý thì không được giữ số 7. */
export function clampPeriodNo(periodType: number, periodNo: number): number {
  const max = countPeriodsInYear(periodType)
  const n = Math.trunc(Number(periodNo))
  if (!Number.isFinite(n) || n < 1) return 1
  return n > max ? max : n
}

/** Các kỳ con của một kỳ. `period_no` ngoài dải được kẹp lại chứ không ném lỗi. */
export function buildSubPeriods(periodType: number, periodNo: number): HeadcountPlanPeriod[] {
  const n = clampPeriodNo(periodType, periodNo)
  switch (periodType) {
    case PLAN_PERIOD_TYPE_CODE.HALF:
      return [quarter(n * 2 - 1), quarter(n * 2)]
    case PLAN_PERIOD_TYPE_CODE.QUARTER:
      return range(n * 3 - 2, n * 3).map(month)
    case PLAN_PERIOD_TYPE_CODE.MONTH:
      return [month(n)]
    default:
      return range(1, 4).map(quarter)
  }
}

/** Các tháng (1..12) thuộc kỳ — dải chọn «Rơi vào tháng» của khoản chi phí. */
export function listPeriodMonths(periodType: number, periodNo: number): number[] {
  return buildSubPeriods(periodType, periodNo).flatMap((p) => p.months)
}

/** Nhãn kỳ như người dùng gọi: «2026» · «H2-2026» · «Q3-2026» · «07/2026». */
export function formatPeriodLabel(periodType: number, periodNo: number, year: number): string {
  const n = clampPeriodNo(periodType, periodNo)
  switch (periodType) {
    case PLAN_PERIOD_TYPE_CODE.HALF:
      return `H${n}-${year}`
    case PLAN_PERIOD_TYPE_CODE.QUARTER:
      return `Q${n}-${year}`
    case PLAN_PERIOD_TYPE_CODE.MONTH:
      return `${String(n).padStart(2, '0')}/${year}`
    default:
      return String(year)
  }
}

/** Ô chọn «Kỳ» theo loại kỳ. Năm chỉ có một kỳ nên trả mảng một phần tử. */
export function buildPeriodNoOptions(periodType: number): { value: string; label: string }[] {
  const max = countPeriodsInYear(periodType)
  return range(1, max).map((n) => {
    switch (periodType) {
      case PLAN_PERIOD_TYPE_CODE.HALF:
        return { value: String(n), label: n === 1 ? 'H1 (6 tháng đầu năm)' : 'H2 (6 tháng cuối năm)' }
      case PLAN_PERIOD_TYPE_CODE.QUARTER:
        return { value: String(n), label: `Quý ${n}` }
      case PLAN_PERIOD_TYPE_CODE.MONTH:
        return { value: String(n), label: `Tháng ${n}` }
      default:
        return { value: '1', label: 'Cả năm' }
    }
  })
}

/**
 * Đổi độ dài mảng định biên khi đổi loại kỳ. Cùng độ dài thì GIỮ NGUYÊN (đổi Q1 sang Q2 của cùng
 * loại Quý vẫn là 3 tháng). Khác độ dài thì kỳ con mới không ánh xạ được sang kỳ con cũ (Q1..Q4 ≠
 * T7..T9), nên mọi ô lấy định biên CUỐI của mảng cũ — con số đích người dùng đã chốt — thay vì cắt
 * ngẫu nhiên theo chỉ số.
 */
export function resizeHeadcounts(headcounts: readonly number[], length: number): number[] {
  if (length <= 0) return []
  if (headcounts.length === length) return [...headcounts]
  const last = headcounts.length ? Math.max(0, Math.trunc(Number(headcounts[headcounts.length - 1]) || 0)) : 0
  return Array.from({ length }, () => last)
}
