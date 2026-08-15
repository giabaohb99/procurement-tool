import { Button } from '@/shared/ui/button'

interface DocumentPriorityToggleProps {
  isImportant: boolean
  isUrgent: boolean
  onChange: (next: { is_important: boolean; is_urgent: boolean }) => void
}

/**
 * Hai nút bật/tắt "Quan trọng" và "Khẩn cấp".
 *
 * Hai cờ ĐỘC LẬP chứ không phải một thang: một văn bản có thể vừa quan trọng
 * vừa khẩn, mà cũng có thứ khẩn nhưng chẳng quan trọng (giấy mời họp chiều
 * nay). Nhét chung một select là mất một trong hai.
 *
 * Khác "Mức độ mật / khẩn" ở khối Thông tin bổ sung: hai mức kia là thang phân
 * loại theo quy định lưu trữ, còn hai cờ này chỉ để lọc nhanh trên danh sách.
 */
export function DocumentPriorityToggle({
  isImportant,
  isUrgent,
  onChange,
}: DocumentPriorityToggleProps) {
  return (
    <div className="flex flex-wrap gap-2">
      <Button
        type="button"
        variant={isImportant ? 'default' : 'outline'}
        aria-pressed={isImportant}
        onClick={() => onChange({ is_important: !isImportant, is_urgent: isUrgent })}
      >
        Quan trọng
      </Button>
      <Button
        type="button"
        variant={isUrgent ? 'default' : 'outline'}
        aria-pressed={isUrgent}
        onClick={() => onChange({ is_important: isImportant, is_urgent: !isUrgent })}
      >
        Khẩn cấp
      </Button>
    </div>
  )
}
