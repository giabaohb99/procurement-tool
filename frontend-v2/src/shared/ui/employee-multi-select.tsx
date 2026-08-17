import type { Employee } from '@/modules/hr/types/employee'
import { MultiPicker } from '@/shared/ui/multi-picker'

interface EmployeeMultiSelectProps {
  /** ID nhân sự đang chọn. */
  value: number[]
  onChange: (ids: number[]) => void
  employees: Employee[]
  placeholder: string
  disabled?: boolean
}

/**
 * Chọn NHIỀU nhân sự — người quản lý sổ, người xem sổ, người duyệt trong luồng.
 *
 * Là lớp mỏng trên `MultiPicker`: phần bấm/tìm/chip giống hệt mọi bộ chọn nhiều
 * mục khác, chỉ khác ở chỗ biết đọc `full_name` và `code` của nhân sự.
 *
 * Không dùng `ScopeEmployeePicker` của phân hệ Nhân sự: component đó mang thêm
 * ngữ nghĩa "không giới hạn / tùy chỉnh" của phạm vi dữ liệu, ở đây danh sách
 * rỗng chỉ đơn giản là chưa cử ai chứ không có nghĩa "mọi người".
 */
export function EmployeeMultiSelect({
  value,
  onChange,
  employees,
  placeholder,
  disabled,
}: EmployeeMultiSelectProps) {
  return (
    <MultiPicker
      value={value}
      onChange={onChange}
      options={employees.map((employee) => ({
        id: employee.id,
        label: employee.full_name,
        hint: employee.code,
      }))}
      placeholder={placeholder}
      searchPlaceholder="Tìm theo tên hoặc mã…"
      emptyMessage="Không tìm thấy nhân sự nào."
      disabled={disabled}
    />
  )
}
