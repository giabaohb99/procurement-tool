import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'

interface ActiveStatusSelectProps {
  value: boolean
  onChange: (value: boolean) => void
  /** Chữ cho hai trạng thái — phòng ban dùng "Hoạt động / Đã ẩn". */
  onLabel?: string
  offLabel?: string
  disabled?: boolean
}

/**
 * Ô chọn Đang dùng / Ngừng. Tách riêng vì cả 3 danh mục (nhân sự, phòng ban,
 * công ty) đều có cột `is_active` và đều phải quy đổi boolean ↔ chuỗi cho Select.
 */
export function ActiveStatusSelect({
  value,
  onChange,
  onLabel = 'Đang dùng',
  offLabel = 'Ngừng / Ẩn',
  disabled,
}: ActiveStatusSelectProps) {
  return (
    <Select
      value={value ? 'true' : 'false'}
      onValueChange={(v) => onChange(v === 'true')}
      disabled={disabled}
    >
      <SelectTrigger className="w-full">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="true">{onLabel}</SelectItem>
        <SelectItem value="false">{offLabel}</SelectItem>
      </SelectContent>
    </Select>
  )
}
