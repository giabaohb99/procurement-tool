import { Label } from '@/shared/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { FILTER_ANY } from '../utils/employee-filter-id'

interface EmployeeFilterSelectProps {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  /** Nhãn của mục đầu "không lọc" (VD "Mọi phòng ban"). */
  anyLabel: string
  options: readonly { value: number; label: string }[]
}

/**
 * Ô chọn MỘT giá trị lọc nhân sự, mục đầu là "Mọi …" (`FILTER_ANY`) — dùng chung cho hộp Cấp quỹ năm
 * và trang Phân bổ hàng loạt (duoc-CR-717). Giá trị là CHUỖI; đổi ra số gửi backend bằng `toFilterId`.
 */
export function EmployeeFilterSelect({ id, label, value, onChange, anyLabel, options }: EmployeeFilterSelectProps) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger id={id} className="w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={FILTER_ANY}>{anyLabel}</SelectItem>
          {options.map((o) => (
            <SelectItem key={o.value} value={String(o.value)}>
              {o.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
