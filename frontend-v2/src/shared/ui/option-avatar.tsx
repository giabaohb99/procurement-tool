import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { cn } from '@/shared/utils/cn'

/**
 * Ảnh nhỏ đầu dòng của ô chọn (người / công ty). Không có ảnh thì hiện chữ cái đầu của nhãn.
 * Dùng chung cho `MultiPicker` và `SearchSelect` — trước đây nằm riêng trong `multi-picker.tsx`.
 */
export function OptionAvatar({ src, label, className }: { src: string; label: string; className?: string }) {
  const initial = (label.trim()[0] || '?').toUpperCase()
  return (
    <Avatar size="sm" className={cn('size-5 shrink-0', className)}>
      {src && <AvatarImage src={src} alt="" className="object-contain" />}
      <AvatarFallback className="text-[10px]">{initial}</AvatarFallback>
    </Avatar>
  )
}
