import type { LeaveBalance } from '../types/leave'

/**
 * Một dòng quỹ phép mẫu cho các bài kiểm.
 *
 * Dùng chung giữa thẻ phân rã và thẻ điều chỉnh: hai thẻ đọc cùng một đối tượng
 * nên chép hai bản là sớm muộn hai bài kiểm nói về hai thứ khác nhau. Số mặc
 * định thỏa đúng công thức của backend — `total = 12 + 2 + 1 + 0 = 15`,
 * `remaining = 15 − 3 − 2 = 10` — nên bài nào đổi một số mà quên đổi số phụ
 * thuộc thì con số vô lý lộ ra ngay.
 */
export function balanceFixture(overrides: Partial<LeaveBalance> = {}): LeaveBalance {
  return {
    id: 5,
    employee_id: 2,
    employee_name: 'Dego Admin',
    year: 2026,
    leave_type_id: 1,
    leave_type_name: 'Phép năm',
    company_id: 1,
    allocated_days: 12,
    seniority_days: 2,
    carried_days: 1,
    adjusted_days: 0,
    used_days: 3,
    pending_days: 2,
    note: '',
    total_days: 15,
    remaining_days: 10,
    ...overrides,
  }
}
