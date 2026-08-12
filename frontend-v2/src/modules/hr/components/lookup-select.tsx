import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'

export interface LookupItem {
  id: number
  label: string
}

interface LookupSelectProps {
  /** 0 hoặc null = chưa chọn. */
  value: number | null
  onChange: (value: number) => void
  items: LookupItem[]
  placeholder: string
  /** Nhãn của mục "bỏ chọn". Bỏ trống = bắt buộc phải chọn. */
  emptyLabel?: string
  disabled?: boolean
}

/**
 * Ô chọn khóa ngoại (phòng ban, trưởng bộ phận, người đại diện…).
 *
 * Backend dùng số 0 làm sentinel "chưa chọn" thay cho NULL, còn Radix Select
 * cấm option có value là chuỗi rỗng — nên quy ước ở đây: chuỗi `"0"` là mục
 * bỏ chọn, mọi giá trị khác là id thật.
 */
export function LookupSelect({
  value,
  onChange,
  items,
  placeholder,
  emptyLabel,
  disabled,
}: LookupSelectProps) {
  return (
    <Select
      value={String(value ?? 0)}
      onValueChange={(next) => onChange(Number(next))}
      disabled={disabled}
    >
      <SelectTrigger className="w-full">
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {emptyLabel && <SelectItem value="0">{emptyLabel}</SelectItem>}
        {items.map((item) => (
          <SelectItem key={item.id} value={String(item.id)}>
            {item.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
