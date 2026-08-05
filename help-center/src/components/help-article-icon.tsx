import { isImageIcon, resolveHelpIcon } from '@/lib/help-icons'
import { cn } from '@/lib/utils'

// Render icon của bài viết — tự phân nhánh giữa icon dựng sẵn (component lucide)
// và ảnh do người soạn tự upload + cắt (thẻ <img> vuông).
// Dùng chung cho thẻ danh mục khu người dùng và ô xem trước ở khu quản trị.

interface HelpArticleIconProps {
  icon: string | null | undefined
  /** Vị trí trong danh sách — chỉ dùng để chọn icon mặc định khi bài chưa gán icon. */
  index?: number
  /** Class kích thước, vd 'size-6'. */
  className?: string
}

export default function HelpArticleIcon({ icon, index = 0, className }: HelpArticleIconProps) {
  if (isImageIcon(icon)) {
    return (
      <img
        src={icon!}
        alt=""
        aria-hidden
        loading="lazy"
        className={cn('rounded-sm object-contain', className)}
      />
    )
  }

  const Icon = resolveHelpIcon(icon, index)
  return <Icon className={className} strokeWidth={1.75} />
}
