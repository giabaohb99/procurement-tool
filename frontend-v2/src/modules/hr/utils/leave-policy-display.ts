import { appRoutes } from '@/shared/constants/app-routes'
import { formatDate } from '@/shared/utils/format-date'
import type {
  LeavePolicyAssignment,
  LeavePolicyLine,
  PolicyBalanceChanges,
  PolicyQuotaChange,
} from '../types/leave-policy'
import { formatCompDays } from './format-comp-days'

/**
 * Hàm thuần dùng chung cho các màn Chính sách nghỉ phép / Phân bổ chính sách (duoc-CR-717):
 * diễn đạt khoảng hiệu lực, thay đổi hạn mức trước → sau, kết quả đụng quỹ năm nay, và sửa danh
 * sách dòng của gói trên bản nháp.
 */

/** Tra tên loại nghỉ theo id — loại đã xóa / ngoài danh sách thì hiện `#id`, không để trống. */
export type LeaveTypeNameLookup = (leaveTypeId: number) => string

export function buildLeaveTypeNameLookup(
  types: readonly { id: number; name: string }[] | undefined,
): LeaveTypeNameLookup {
  const names = new Map((types ?? []).map((t) => [t.id, t.name]))
  return (id) => names.get(id) || `#${id}`
}

/** "01/07/2026 → 31/12/2026" hoặc "01/07/2026 → Không thời hạn". */
export function formatPolicyRange(from: string, to: string | null | undefined): string {
  return `${formatDate(from)} → ${to ? formatDate(to) : 'Không thời hạn'}`
}

/** "Phép năm 12 → 15" — mỗi loại một cụm, nối bằng dấu chấm phẩy. Rỗng = "Không đổi". */
export function summarizeQuotaChanges(
  changes: readonly PolicyQuotaChange[],
  typeName: LeaveTypeNameLookup,
): string {
  const moved = changes.filter((c) => c.before !== c.after)
  if (moved.length === 0) return 'Không đổi'
  return moved
    .map((c) => `${typeName(c.leave_type_id)} ${formatCompDays(c.before)} → ${formatCompDays(c.after)}`)
    .join('; ')
}

/**
 * Câu báo sau một lượt ghi: quỹ năm nay đã đụng tới đâu. Nói rõ cả trường hợp KHÔNG đụng gì —
 * người bỏ tick "Tính lại" cần biết quỹ đã cấp được giữ nguyên, không phải hệ thống quên.
 */
export function describeBalanceChanges(balances: PolicyBalanceChanges | undefined): string {
  if (!balances) return ''
  const parts: string[] = []
  if (balances.recalculated.length) parts.push(`tính lại ${balances.recalculated.length} dòng quỹ`)
  if (balances.created) parts.push(`cấp mới ${balances.created} dòng quỹ`)
  if (balances.kept) parts.push(`giữ nguyên ${balances.kept} dòng quỹ`)
  if (parts.length === 0) return 'Quỹ phép năm nay không đổi.'
  const text = `Quỹ phép năm nay: ${parts.join(', ')}.`
  return balances.negative_after.length
    ? `${text} ${balances.negative_after.length} dòng quỹ bị ÂM sau khi tính lại — kiểm tra ở màn Quỹ phép năm.`
    : text
}

/** Bước nhập số ngày của dòng gói — backend nhận 0–366, bước 0,5. */
export const POLICY_DAYS_MAX = 366
export const POLICY_LINES_MAX = 50

/**
 * Đọc ô "Số ngày mỗi năm" (ô CHỮ, không phải `type=number` — review M3): nhận dấu phẩy thập phân kiểu Việt
 * ("12,5") lẫn dấu chấm, bỏ khoảng trắng hai đầu. Rỗng / không phải số → `null` để thẻ báo "Nhập số ngày";
 * `Number('')` = 0 từng lẳng lặng thêm một dòng 0 ngày. Khoảng 0–366 và bước 0,5 kiểm ở `upsertPolicyLine`.
 */
export function parsePolicyDays(raw: string): number | null {
  const text = raw.trim()
  if (!/^-?\d+(?:[.,]\d+)?$/.test(text)) return null
  return Number(text.replace(',', '.'))
}

/**
 * Thêm một dòng vào bản nháp, TRÙNG loại nghỉ thì ghi đè dòng cũ (một loại chỉ một dòng — backend
 * 422 nếu trùng). Trả `error` thay vì ném để thẻ hiện thẳng cho người khai.
 */
export function upsertPolicyLine(
  lines: readonly LeavePolicyLine[],
  next: LeavePolicyLine,
): { lines: LeavePolicyLine[]; error: string | null } {
  const current = [...lines]
  if (!Number.isInteger(next.leave_type_id) || next.leave_type_id <= 0) {
    return { lines: current, error: 'Chọn loại nghỉ.' }
  }
  const days = next.annual_days
  if (!Number.isFinite(days) || days < 0 || days > POLICY_DAYS_MAX) {
    return { lines: current, error: `Số ngày mỗi năm phải từ 0 đến ${POLICY_DAYS_MAX}.` }
  }
  if (Math.abs(days * 2 - Math.round(days * 2)) > 1e-9) {
    return { lines: current, error: 'Số ngày tính theo bước 0,5 (VD 12 hoặc 12,5).' }
  }
  const index = current.findIndex((l) => l.leave_type_id === next.leave_type_id)
  if (index >= 0) {
    current[index] = { ...current[index], annual_days: days }
    return { lines: current, error: null }
  }
  if (current.length >= POLICY_LINES_MAX) {
    return { lines: current, error: `Một chính sách tối đa ${POLICY_LINES_MAX} loại nghỉ.` }
  }
  return { lines: [...current, { leave_type_id: next.leave_type_id, annual_days: days }], error: null }
}

/**
 * Đường sang danh sách phân bổ đã lọc đúng chính sách (+ đúng người nếu có dòng) — tab "Đang phân bổ"
 * của chi tiết chính sách bấm dòng là sang đây. Tên tham số khớp ô lọc của trang danh sách.
 */
export function buildAssignmentListHref(
  policyId: number,
  row?: Pick<LeavePolicyAssignment, 'employee_code'>,
): string {
  const params = new URLSearchParams({ policy_id: String(policyId) })
  if (row?.employee_code) params.set('q', row.employee_code)
  return `${appRoutes.hr.leavePolicyAssignments}?${params.toString()}`
}
