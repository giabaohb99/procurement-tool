import { X } from 'lucide-react'
import { useState } from 'react'

import { cn } from '@/shared/utils/cn'

/** Số chip hiện sẵn trước khi gộp phần còn lại vào nút "+N nữa". */
const CHIP_LIMIT = 12

interface SubjectChipsProps {
  items: { key: string; label: string }[]
  /** Bỏ trống = dải CHỈ ĐỌC (hộp «Sửa quyền cụm» chỉ để rà lại, không xóa ở đó). */
  onRemove?: (key: string) => void
}

/**
 * Dải chip đối tượng, xóa được từng cái. Dùng chung cho hộp chia quyền và khối
 * quyền truy cập ngoài form — hai chỗ đó phải nhìn y hệt nhau.
 *
 * Chống vỡ khi cụm đông: tên dài bị cắt bớt, quá `CHIP_LIMIT` chip thì phần dư
 * gộp vào một nút đếm, bung ra thì dải tự cuộn trong khung cao cố định. Không
 * có mấy chốt này thì một cụm 50 người đẩy nút Xong xuống dưới đáy màn hình.
 */
export function SubjectChips({ items, onRemove }: SubjectChipsProps) {
  const [expanded, setExpanded] = useState(false)
  const shown = expanded ? items : items.slice(0, CHIP_LIMIT)
  const hidden = items.length - shown.length

  return (
    <div className={cn('flex flex-wrap gap-1.5', expanded && 'max-h-32 overflow-y-auto')}>
      {shown.map((item) => (
        <span
          key={item.key}
          className={cn(
            'inline-flex max-w-44 items-center gap-1 rounded-md border py-0.5 pl-2 text-xs',
            onRemove ? 'pr-1' : 'pr-2',
          )}
        >
          <span className="truncate">{item.label}</span>
          {onRemove && (
            <button
              type="button"
              title={`Bỏ ${item.label}`}
              aria-label={`Bỏ ${item.label}`}
              onClick={() => onRemove(item.key)}
              className="shrink-0 rounded-sm p-0.5 text-muted-foreground hover:bg-muted focus-visible:outline-none"
            >
              <X className="size-3" />
            </button>
          )}
        </span>
      ))}

      {(hidden > 0 || expanded) && (
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="rounded-md px-2 py-0.5 text-xs text-muted-foreground underline-offset-2 hover:underline"
        >
          {expanded ? 'Thu gọn' : `+${hidden} nữa`}
        </button>
      )}
    </div>
  )
}
