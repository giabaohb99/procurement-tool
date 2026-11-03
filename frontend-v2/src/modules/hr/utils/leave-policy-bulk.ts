import type { PolicyPreviewItem, PolicyPreviewPayload } from '../types/leave-policy'
import { FILTER_ANY, toFilterId } from './employee-filter-id'

/**
 * Hàm thuần của trang PHÂN BỔ HÀNG LOẠT (duoc-CR-717, kiểu Leave Control Panel của ERPNext).
 */

/** Trần một lượt (khớp `MAX_BULK` backend). */
export const BULK_MAX = 500

export interface BulkSettings {
  policyId: number
  from: string
  to: string
  recalc: boolean
  closePrevious: boolean
  companyId: string
  departmentId: string
  employmentType: string
  jobLevel: string
  onlyWithoutActive: boolean
}

export function createBulkSettings(today: string): BulkSettings {
  return {
    policyId: 0,
    from: today,
    to: '',
    recalc: true,
    closePrevious: false,
    companyId: FILTER_ANY,
    departmentId: FILTER_ANY,
    employmentType: FILTER_ANY,
    jobLevel: FILTER_ANY,
    onlyWithoutActive: true,
  }
}

/** Lý do chưa xem trước được (thiếu chính sách / ngày, khoảng ngày ngược) — rỗng = được. */
export function validateBulkSettings(s: BulkSettings): string {
  if (s.policyId <= 0) return 'Chọn chính sách.'
  if (!s.from) return 'Chọn "Từ ngày".'
  if (s.to && s.to < s.from) return '"Đến ngày" không được trước "Từ ngày".'
  return ''
}

/** Thân `/preview` theo bộ lọc. Ô tick "Tính lại" KHÔNG nằm ở đây — nó không đổi kết quả xem trước. */
export function buildBulkPreviewPayload(s: BulkSettings): PolicyPreviewPayload {
  const payload: PolicyPreviewPayload = {
    policy_id: s.policyId,
    effective_from: s.from,
    effective_to: s.to || null,
    close_previous: s.closePrevious,
    only_without_active: s.onlyWithoutActive,
  }
  const filters = {
    company_id: toFilterId(s.companyId),
    department_id: toFilterId(s.departmentId),
    employment_type: toFilterId(s.employmentType),
    job_level: toFilterId(s.jobLevel),
  }
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined) payload[key as keyof typeof filters] = value
  }
  return payload
}

/**
 * Chữ ký của một lượt xem trước — so với chữ ký của bộ ô HIỆN TẠI để biết danh sách đang hiện có còn
 * khớp không. Đổi chính sách / ngày / lọc sau khi xem mà vẫn cho bấm Phân bổ là gán theo số cũ.
 */
export function bulkPreviewSignature(s: BulkSettings): string {
  return JSON.stringify(buildBulkPreviewPayload(s))
}

/** Dòng chọn được = dòng KHÔNG vướng (chồng ngày / tự phân bổ / gói ngừng). */
export function selectableEmployeeIds(items: readonly PolicyPreviewItem[]): number[] {
  return items.filter((i) => !i.conflict).map((i) => i.employee_id)
}
