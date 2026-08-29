import { Tag } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'
import type { WorkLabelField } from '../types/work'
import { chipClass } from '../utils/work-colors'

interface LabelMultiCellProps {
  field: WorkLabelField
  chosen: number[]
  disabled?: boolean
  onChange: (value: number[] | null) => void
}

/**
 * Trường CHỌN NHIỀU thu về vừa MỘT ô bảng ở khung nhìn Danh sách.
 *
 * Bản dùng ở panel chi tiết bày thẳng mọi giá trị của trường thành một dải chip
 * bật/tắt — đọc rất nhanh khi có cả chiều ngang panel, nhưng nhét vào ô rộng
 * 150px thì trường bốn giá trị đã xuống hai hàng và mọi dòng của bảng cao gấp
 * đôi, kể cả dòng không gắn giá trị nào. Ở đây chỉ hiện thứ ĐANG gắn; muốn đổi
 * thì mở popover, và trong popover vẫn là đúng dải chip quen thuộc ấy.
 */
export function LabelMultiCell({ field, chosen, disabled, onChange }: LabelMultiCellProps) {
  const [open, setOpen] = useState(false)
  const picked = field.options.filter((o) => chosen.includes(o.id))

  function toggle(optionId: number) {
    const next = chosen.includes(optionId)
      ? chosen.filter((id) => id !== optionId)
      : [...chosen, optionId]
    onChange(next.length === 0 ? null : next)
  }

  /*  Chỉ vẽ MỘT chip rồi dồn phần còn lại vào «+N»: ô rộng 150px mà hai chip
      tiếng Việt là đã tràn, còn cho xuống dòng thì mọi dòng của bảng cao gấp
      đôi. Tên đầy đủ của phần bị dồn nằm ở `title`, và mở popover là thấy hết.  */
  const faces = picked.length ? (
    <span className="flex min-w-0 items-center gap-1">
      <span
        className={cn(
          'truncate rounded px-1.5 py-0.5 text-[11px] font-medium',
          chipClass(picked[0].color),
        )}
      >
        {picked[0].name}
      </span>
      {picked.length > 1 && (
        <span
          title={picked
            .slice(1)
            .map((o) => o.name)
            .join(', ')}
          className="shrink-0 rounded bg-muted px-1 py-0.5 text-[11px] text-muted-foreground"
        >
          +{picked.length - 1}
        </span>
      )}
    </span>
  ) : null

  if (disabled) {
    return faces ?? <span className="text-xs text-muted-foreground">—</span>
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          aria-label={field.name}
          className="flex h-6 w-full items-center gap-1 rounded px-1 text-left hover:bg-accent"
        >
          {faces ?? (
            <Tag className="size-3.5 text-muted-foreground opacity-0 transition-opacity group-hover/row:opacity-60" />
          )}
        </button>
      </PopoverTrigger>

      <PopoverContent align="start" className="w-60 p-2">
        {field.options.length === 0 ? (
          <p className="py-2 text-center text-sm text-muted-foreground">
            Trường chưa khai giá trị
          </p>
        ) : (
          <>
            <div className="flex flex-wrap gap-1">
              {field.options.map((o) => (
                <button
                  key={o.id}
                  type="button"
                  onClick={() => toggle(o.id)}
                  className={cn(
                    'cursor-pointer rounded px-1.5 py-0.5 text-[11px] font-medium transition-opacity hover:opacity-100',
                    chipClass(o.color),
                    !chosen.includes(o.id) && 'opacity-35',
                  )}
                >
                  {o.name}
                </button>
              ))}
            </div>
            {chosen.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="mt-2 h-7 w-full text-muted-foreground"
                onClick={() => onChange(null)}
              >
                Bỏ chọn hết
              </Button>
            )}
          </>
        )}
      </PopoverContent>
    </Popover>
  )
}
