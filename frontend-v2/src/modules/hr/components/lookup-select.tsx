import { SearchSelect } from '@/shared/ui/search-select'

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
  /** Gắn lên ô chọn để `<Label htmlFor>` trỏ tới được. */
  id?: string
}

/** Giá trị của mục "bỏ chọn" — backend dùng số 0 làm sentinel "chưa chọn" thay cho NULL. */
const EMPTY_VALUE = '0'

/**
 * Ô chọn khóa ngoại (công ty, phòng ban, chức vụ, người quản lý, trưởng bộ phận…) — CÓ Ô TÌM.
 *
 * duoc-CR-747 (11/11/2026): trước đây là Radix Select thuần, không gõ tìm được; ô *Người quản lý trực tiếp* phải cuộn
 * qua vài trăm tên. Nay dựng trên `SearchSelect` (tìm không dấu, khớp cả nhãn), giữ nguyên giao diện props nên mọi
 * nơi gọi không đổi.
 *
 * **Danh sách luôn chứa giá trị đang chọn** (`fallbackLabel`): danh mục ở đây lọc theo pháp nhân, mà dữ liệu cũ có
 * phòng ở pháp nhân này lại giữ trưởng phòng của pháp nhân khác — không có nhãn dự phòng thì ô hiện trống, người đọc
 * hiểu thành "chưa chỉ định" rồi lưu đè lên.
 */
export function LookupSelect({
  value,
  onChange,
  items,
  placeholder,
  emptyLabel,
  fallbackLabel,
  disabled,
  id,
}: LookupSelectProps) {
  const existing = !value || items.some((item) => item.id === value)
  const list = existing ? items : [{ id: value, label: fallbackLabel || `#${value}` }, ...items]
  const options = [
    ...(emptyLabel ? [{ value: EMPTY_VALUE, label: emptyLabel }] : []),
    ...list.map((item) => ({ value: String(item.id), label: item.label })),
  ]

  return (
    <SearchSelect
      id={id}
      //  Chưa chọn mà không có mục "bỏ chọn" thì để rỗng cho ô hiện chữ gợi ý (như Radix Select cũ).
      value={value ? String(value) : emptyLabel ? EMPTY_VALUE : ''}
      onChange={(next) => onChange(Number(next) || 0)}
      options={options}
      placeholder={placeholder}
      searchPlaceholder="Gõ để tìm…"
      emptyMessage="Không tìm thấy mục nào."
      disabled={disabled}
    />
  )
}
