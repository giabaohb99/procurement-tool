/**
 * Luật của bảng Phân công phụ trách — bao-CR-527 (khách chốt 30/09/2026).
 *
 * Đúng 1 NSTM chính (bắt buộc) + tối đa 1 dự phòng (khác người chính), cả hai phải «Chính
 * thức» và đang hoạt động. Backend chặn thật ở `category_assignee.service.validate_assignee_pair`
 * (mọi cửa ghi); ở đây chỉ để ô chọn không mời người không hợp lệ và để bấm Lưu báo ngay tại chỗ.
 */

/** Mã «Chính thức» của `tab_employee.status` — bộ mã sinh ở `shared/constants/statuses.ts`. */
export const OFFICIAL_EMPLOYEE_STATUS = 'official'

export interface AssigneeEmployee {
  id: number
  full_name: string
  code?: string | null
  status?: string | null
  status_label?: string | null
  is_active?: boolean | null
}

export interface AssigneeOption {
  value: number
  label: string
  /** Còn nhận việc được không — mục `false` chỉ giữ lại cho người ĐANG được gán. */
  official: boolean
}

/** «Chính thức» + đang hoạt động. Thiếu mã trạng thái thì KHÔNG tính (không đoán). */
export function isOfficialEmployee(employee: AssigneeEmployee | null | undefined): boolean {
  if (!employee) return false
  return employee.is_active !== false && employee.status === OFFICIAL_EMPLOYEE_STATUS
}

/** Tình trạng để nói trong câu chặn / nhãn cảnh báo. */
export function employeeStatusText(employee: AssigneeEmployee): string {
  if (employee.is_active === false) return 'ngừng hoạt động'
  return employee.status_label || employee.status || 'chưa rõ'
}

/**
 * Mục chọn cho hai ô NSTM: chỉ người «Chính thức» đang hoạt động. Người ĐANG được gán mà nay không
 * còn đạt (nghỉ thai sản, nghỉ việc…) vẫn được giữ trong danh sách kèm tình trạng — không thì ô
 * hiện trống và người sửa không biết dòng này đang giao cho ai.
 */
export function assigneeOptions(employees: AssigneeEmployee[], keepIds: number[] = []): AssigneeOption[] {
  const keep = new Set(keepIds.filter(Boolean))
  return employees
    .filter((e) => isOfficialEmployee(e) || keep.has(e.id))
    .map((e) => {
      const official = isOfficialEmployee(e)
      const base = `${e.full_name}${e.code ? ` · ${e.code}` : ''}`
      return { value: e.id, label: official ? base : `${base} (${employeeStatusText(e)})`, official }
    })
}

/**
 * Câu chặn khi bấm Lưu; `null` = hợp lệ. `employees` để kiểm tình trạng người đã chọn — người
 * không có trong danh mục đã nạp thì để backend nói (không đoán).
 */
export function validateAssigneePair(
  primaryId: number,
  backupId: number,
  employees: AssigneeEmployee[] = [],
): string | null {
  if (!primaryId) return 'Vui lòng chọn NSTM chính'
  if (backupId && backupId === primaryId) return 'NSTM dự phòng phải là người khác NSTM chính'
  const byId = new Map(employees.map((e) => [e.id, e]))
  for (const [id, role] of [
    [primaryId, 'NSTM chính'],
    [backupId, 'NSTM dự phòng'],
  ] as const) {
    const employee = id ? byId.get(id) : undefined
    if (employee && !isOfficialEmployee(employee)) {
      return `${role} ${employee.full_name} đang ở tình trạng «${employeeStatusText(employee)}» — chỉ phân công được nhân sự «Chính thức» đang hoạt động`
    }
  }
  return null
}
