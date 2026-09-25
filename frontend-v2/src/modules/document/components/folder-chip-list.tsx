import { Folder, Star, X } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { cn } from '@/shared/utils/cn'

export interface FolderChipItem {
  id: number
  name: string
}

interface FolderChipListProps {
  items: FolderChipItem[]
  /** Id thư mục CHÍNH — chỉ có ý nghĩa khi `items.length > 1`. */
  primaryId?: number | null
  onRemove: (id: number) => void
  /** Bỏ trống = ẩn hẳn ngôi sao (chế độ chọn MỘT thư mục, không có khái niệm chính/phụ). */
  onSetPrimary?: (id: number) => void
  disabled?: boolean
  className?: string
}

/**
 * Hàng CHIP của thư mục đã chọn — chip đầu tiên theo THỨ TỰ `items` là thư mục
 * CHÍNH khi không truyền `primaryId` tường minh, nhưng nơi gọi (`folder-picker.tsx`)
 * luôn truyền `primaryId` rõ ràng nên không dựa vào quy ước đó.
 *
 * Ngôi sao chỉ hiện khi có từ HAI thư mục trở lên — một thư mục thì "chính"
 * không có ý nghĩa gì để chọn.
 */
export function FolderChipList({
  items,
  primaryId,
  onRemove,
  onSetPrimary,
  disabled,
  className,
}: FolderChipListProps) {
  if (items.length === 0) return null

  const showStars = Boolean(onSetPrimary) && items.length > 1

  return (
    <div className={cn('flex flex-wrap gap-1.5', className)}>
      {items.map((item) => {
        const isPrimary = item.id === primaryId
        return (
          <Badge
            key={item.id}
            variant={isPrimary ? 'default' : 'outline'}
            className="gap-1 py-1 pr-1 pl-2 font-normal"
          >
            <Folder className="size-3" />
            <span className="max-w-48 truncate">{item.name}</span>

            {showStars && (
              <button
                type="button"
                disabled={disabled}
                title={isPrimary ? 'Thư mục chính' : 'Đặt làm thư mục chính'}
                aria-label={isPrimary ? 'Thư mục chính' : `Đặt "${item.name}" làm thư mục chính`}
                aria-pressed={isPrimary}
                onClick={() => onSetPrimary?.(item.id)}
                className={cn(
                  'flex size-4 shrink-0 items-center justify-center rounded-full hover:bg-black/10',
                  disabled && 'pointer-events-none opacity-50',
                )}
              >
                <Star className={cn('size-3', isPrimary && 'fill-current')} />
              </button>
            )}

            <button
              type="button"
              disabled={disabled}
              title="Gỡ khỏi thư mục này"
              aria-label={`Gỡ "${item.name}" khỏi danh sách thư mục`}
              onClick={() => onRemove(item.id)}
              className={cn(
                'flex size-4 shrink-0 items-center justify-center rounded-full hover:bg-black/10',
                disabled && 'pointer-events-none opacity-50',
              )}
            >
              <X className="size-3" />
            </button>
          </Badge>
        )
      })}
    </div>
  )
}
