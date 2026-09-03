import { FORUM_PREFIX, labelOf } from '@/shared/constants/statuses'
import { cn } from '@/shared/utils/cn'

// why: bộ mã `forum_prefix` sinh từ backend chỉ mang value + label; MÀU là
// chuyện thuần hiển thị nên khai tại đây (kiểu chip prefix của VOZ) — thêm
// prefix mới bên backend thì thêm một dòng màu, thiếu dòng rơi về xám.
const PREFIX_CHIP_CLASSES: Record<string, string> = {
  '1': 'bg-blue-500/15 text-blue-700 dark:text-blue-400', // Thảo luận
  '2': 'bg-amber-500/15 text-amber-700 dark:text-amber-400', // Thắc mắc
  '3': 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400', // Kiến thức
  '4': 'bg-pink-500/15 text-pink-700 dark:text-pink-400', // Khoe
  '5': 'bg-violet-500/15 text-violet-700 dark:text-violet-400', // Đánh giá
}

interface ThreadPrefixChipProps {
  /** Giá trị `prefix` của bài — 0/không nhãn thì component tự ẩn. */
  prefix: number
  className?: string
}

/** Chip prefix màu đứng trước tiêu đề thread (F13b) — nhãn lấy từ bộ mã sinh. */
export function ThreadPrefixChip({ prefix, className }: ThreadPrefixChipProps) {
  const label = labelOf(FORUM_PREFIX, String(prefix))
  if (prefix <= 0 || !label) return null
  return (
    <span
      className={cn(
        'inline-flex shrink-0 items-center rounded px-1.5 py-0.5 text-[11px] font-semibold whitespace-nowrap',
        PREFIX_CHIP_CLASSES[String(prefix)] ?? 'bg-muted text-muted-foreground',
        className,
      )}
    >
      {label}
    </span>
  )
}
