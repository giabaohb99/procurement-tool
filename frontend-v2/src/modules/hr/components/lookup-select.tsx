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
  /**
   * Tên của giá trị ĐANG LƯU, để hiện khi nó chưa (hoặc không) có trong `items`.
   *
   * Trang chi tiết luôn có sẵn tên này từ chính bản ghi (`manager_name`,
   * `department_name`…). Bỏ trống thì ô hiện `#<id>` — vẫn hơn là hiện trống.
   */
  fallbackLabel?: string
  disabled?: boolean
}

/**
 * Ô chọn khóa ngoại (phòng ban, trưởng bộ phận, người đại diện…).
 *
 * Backend dùng số 0 làm sentinel "chưa chọn" thay cho NULL, còn Radix Select
 * cấm option có value là chuỗi rỗng — nên quy ước ở đây: chuỗi `"0"` là mục
 * bỏ chọn, mọi giá trị khác là id thật.
 *
 * **Danh sách luôn chứa giá trị đang chọn** (`fallbackLabel`): danh mục ở đây
 * lọc theo pháp nhân, mà dữ liệu cũ có phòng ở pháp nhân này lại giữ trưởng
 * phòng của pháp nhân khác — không có nhãn dự phòng thì ô hiện trống, người đọc
 * hiểu thành «chưa chỉ định».
 *
 * Chỗ mất dữ liệu đi kèm (chuỗi rỗng do thẻ `<select>` ẩn của Radix bắn ra khi
 * danh mục về muộn) đã vá ở `shared/ui/select.tsx` — đọc chú thích ở đó.
 */
export function LookupSelect({
  value,
  onChange,
  items,
  placeholder,
  emptyLabel,
  fallbackLabel,
  disabled,
}: LookupSelectProps) {
  const daCo = !value || items.some((item) => item.id === value)
  const danhSach = daCo
    ? items
    : [{ id: value, label: fallbackLabel || `#${value}` }, ...items]

  return (
    <Select
      value={String(value ?? 0)}
      //  Chuỗi rỗng do thẻ `<select>` ẩn của Radix bắn ra đã bị chặn ở
      //  `shared/ui/select.tsx` — đọc chú thích ở đó trước khi đụng vào.
      onValueChange={(next) => onChange(Number(next))}
      disabled={disabled}
    >
      <SelectTrigger className="w-full">
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {emptyLabel && <SelectItem value="0">{emptyLabel}</SelectItem>}
        {danhSach.map((item) => (
          <SelectItem key={item.id} value={String(item.id)}>
            {item.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
