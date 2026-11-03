import { EMPLOYMENT_TYPE_OPTIONS, JOB_LEVEL_OPTIONS } from '../types/employee-codes'
import { LEAVE_QUOTA_BASIS, type LeaveTypeQuotaRule } from '../types/leave'

/** Trần số dòng hạn mức của một loại nghỉ — khớp `QuotaRuleReplace.max_length` ở backend. */
export const MAX_QUOTA_RULES = 50

export const QUOTA_BASIS_LABELS: Record<number, string> = {
  [LEAVE_QUOTA_BASIS.EMPLOYMENT_TYPE]: 'Hình thức nhân viên',
  [LEAVE_QUOTA_BASIS.JOB_LEVEL]: 'Cấp bậc',
}

/** Các mã chọn được của một cơ sở (bỏ mã 0 «chưa khai»). */
export function quotaValueOptions(basis: number): { value: number; label: string }[] {
  const source =
    basis === LEAVE_QUOTA_BASIS.EMPLOYMENT_TYPE ? EMPLOYMENT_TYPE_OPTIONS : JOB_LEVEL_OPTIONS
  return source.filter((option) => option.value > 0)
}

/** Tên nhóm của một dòng, VD «Hình thức nhân viên: Bán thời gian». */
export function describeQuotaRule(rule: Pick<LeaveTypeQuotaRule, 'basis' | 'basis_value'>): string {
  const label = quotaValueOptions(rule.basis).find((o) => o.value === rule.basis_value)?.label
  return `${QUOTA_BASIS_LABELS[rule.basis] ?? 'Nhóm'}: ${label ?? `#${rule.basis_value}`}`
}

/** Xếp ổn định: hình thức nhân viên trước cấp bậc, rồi theo mã. */
export function sortQuotaRules(rules: LeaveTypeQuotaRule[]): LeaveTypeQuotaRule[] {
  return [...rules].sort((a, b) => a.basis - b.basis || a.basis_value - b.basis_value)
}

/**
 * Thêm hoặc ghi đè dòng của cùng nhóm (một nhóm chỉ một dòng — backend 422 nếu trùng).
 * Trả `error` thay vì ném để thẻ hiện thẳng cho người khai.
 */
export function upsertQuotaRule(
  rules: LeaveTypeQuotaRule[],
  next: LeaveTypeQuotaRule,
): { rules: LeaveTypeQuotaRule[]; error: string | null } {
  if (!Number.isFinite(next.quota_days) || next.quota_days < 0 || next.quota_days > 366) {
    return { rules, error: 'Số ngày phải từ 0 đến 366.' }
  }
  if (next.basis_value <= 0) return { rules, error: 'Chọn nhóm áp dụng.' }
  const others = rules.filter((r) => !(r.basis === next.basis && r.basis_value === next.basis_value))
  if (others.length >= MAX_QUOTA_RULES) {
    return { rules, error: `Tối đa ${MAX_QUOTA_RULES} dòng hạn mức.` }
  }
  return { rules: sortQuotaRules([...others, next]), error: null }
}
