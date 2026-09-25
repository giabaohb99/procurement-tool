import { Checkbox } from '@/shared/ui/checkbox'
import { cn } from '@/shared/utils/cn'

interface FolderItemSelectCheckboxProps {
  checked: boolean | 'indeterminate'
  onToggle: () => void
  /** Tên hỗ trợ — «Chọn ‹tên›» / «Chọn tất cả». */
  label: string
  className?: string
}

/**
 * Ô TICK chọn một mục ở khung nội dung thư mục (chốt 24/09/2026: chọn bằng ô
 * tick thay vì bắt người dùng nhớ Shift/Ctrl — bấm thân dòng/thẻ nay là MỞ).
 *
 * ⚠️ Chặn `click`/`keydown` nổi bọt lên dòng/thẻ cha: không chặn thì bấm
 * tick = vừa chọn vừa MỞ (đi sang trang khác), Enter trên ô tick mở luôn mục
 * đó. Không được đặt BÊN TRONG một `<button>` (nút lồng nút, HTML sai) — thẻ
 * thư mục là `<button>` nên đặt ô tick làm anh em, định vị tuyệt đối.
 */
export function FolderItemSelectCheckbox({
  checked,
  onToggle,
  label,
  className,
}: FolderItemSelectCheckboxProps) {
  return (
    <span
      className={cn('flex items-center', className)}
      onClick={(event) => event.stopPropagation()}
      onKeyDown={(event) => event.stopPropagation()}
    >
      <Checkbox checked={checked} onCheckedChange={onToggle} aria-label={label} />
    </span>
  )
}
