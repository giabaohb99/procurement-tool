import {
  EMPTY_EMPLOYEE_WORK_HISTORY_FORM,
  type EmployeeWorkHistoryFormValues,
} from '../schemas/employee-work-history-schema'
import type { Employee } from '../types/employee'
import type { EmployeeWorkHistory } from '../types/employee-work-history'

/**
 * Giá trị khởi tạo của hộp thêm/sửa — tách khỏi
 * `employee-work-history-form-dialog.tsx` để tệp đó giữ dưới ~200 dòng
 * (CLAUDE.md §"File Size Management"). Hàm THUẦN, không gọi API.
 *
 * SỬA dòng có sẵn → chép nguyên dòng đó. TẠO MỚI → điền sẵn từ hồ sơ hiện tại,
 * `seed` (vd nút «Tạo dòng đầu từ hồ sơ») đè lên sau cùng.
 */
export function buildEmployeeWorkHistoryDefaultValues(
  employee: Employee,
  row: EmployeeWorkHistory | null | undefined,
  seed?: Partial<EmployeeWorkHistoryFormValues>,
): EmployeeWorkHistoryFormValues {
  if (row) {
    return {
      event_type: row.event_type,
      from_date: row.from_date,
      to_date: row.to_date ?? '',
      company_id: row.company_id,
      department_id: row.department_id,
      position_id: row.position_id,
      decision_no: row.decision_no,
      decision_date: row.decision_date ?? '',
      note: row.note,
      close_open_main: false,
    }
  }
  return {
    ...EMPTY_EMPLOYEE_WORK_HISTORY_FORM,
    company_id: employee.company_id,
    department_id: employee.department_id,
    position_id: employee.position_id ?? 0,
    ...seed,
  }
}
