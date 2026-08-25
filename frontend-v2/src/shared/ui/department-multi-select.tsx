import type { Department } from '@/modules/hr/types/department'
import { MultiPicker } from '@/shared/ui/multi-picker'

interface DepartmentMultiSelectProps {
  /** ID phòng ban đang chọn. */
  value: number[]
  onChange: (ids: number[]) => void
  departments: Department[]
  placeholder: string
  disabled?: boolean
}

/**
 * Chọn NHIỀU phòng ban — dùng cho bước duyệt «trưởng bộ phận của phòng ban chỉ định».
 *
 * Là lớp mỏng trên `MultiPicker`, cùng khuôn với `EmployeeMultiSelect`: phần
 * bấm / tìm / chip giống hệt mọi bộ chọn nhiều mục khác, chỉ khác ở chỗ biết đọc
 * `name` và `manager_name` của phòng ban.
 *
 * Gợi ý phụ là TÊN TRƯỞNG BỘ PHẬN chứ không phải mã phòng: người khai luồng
 * đang chọn cái GHẾ, nên thứ họ cần đối chiếu là "ghế đó hiện ai ngồi". Phòng
 * chưa có trưởng thì nói thẳng — chọn vào đó là bước không tìm được ai duyệt.
 */
export function DepartmentMultiSelect({
  value,
  onChange,
  departments,
  placeholder,
  disabled,
}: DepartmentMultiSelectProps) {
  return (
    <MultiPicker
      value={value}
      onChange={onChange}
      options={departments.map((department) => ({
        id: department.id,
        label: department.name,
        hint: department.manager_name || '(chưa có trưởng bộ phận)',
      }))}
      placeholder={placeholder}
      searchPlaceholder="Tìm theo tên phòng ban…"
      emptyMessage="Không tìm thấy phòng ban nào."
      disabled={disabled}
    />
  )
}
