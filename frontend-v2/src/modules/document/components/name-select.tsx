import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'

/** Radix cấm option mang giá trị chuỗi rỗng, nên "chưa chọn" phải có mã riêng. */
const NONE = '__none__'

interface NameSelectProps {
  /** Chuỗi rỗng = chưa chọn. */
  value: string
  onChange: (value: string) => void
  /** Danh sách tên để chọn — xem `hooks/use-document-people.ts`. */
  options: string[]
  placeholder: string
  /** Nhãn của mục bỏ chọn, vd "-- Mặc định --". */
  emptyLabel?: string
  disabled?: boolean
}

/**
 * Ô chọn mà GIÁ TRỊ CHÍNH LÀ TÊN hiện trên màn hình (người xử lý, đơn vị soạn
 * thảo…).
 *
 * Khác `LookupSelect` của phân hệ Nhân sự (lưu id): phân hệ Văn bản chưa có
 * backend nên không giữ được khóa ngoại, lưu tên là thứ đọc được ngay ở sổ văn
 * bản lẫn bản in mà không phải tra bảng.
 */
export function NameSelect({
  value,
  onChange,
  options,
  placeholder,
  emptyLabel,
  disabled,
}: NameSelectProps) {
  return (
    <Select
      value={value || NONE}
      onValueChange={(next) => onChange(next === NONE ? '' : next)}
      disabled={disabled}
    >
      <SelectTrigger className="w-full">
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {emptyLabel && <SelectItem value={NONE}>{emptyLabel}</SelectItem>}

        {/* Tên đã lưu nhưng không còn trong danh sách (người đã nghỉ việc) vẫn
            phải hiện ra, nếu không mở bản ghi cũ lên là ô trống trơn. */}
        {value && !options.includes(value) && <SelectItem value={value}>{value}</SelectItem>}

        {options.map((option) => (
          <SelectItem key={option} value={option}>
            {option}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
