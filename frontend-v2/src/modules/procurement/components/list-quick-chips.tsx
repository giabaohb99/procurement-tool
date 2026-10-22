import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'

export interface QuickChip {
  label: string
  active: boolean
  onToggle: () => void
  /** Có lý do thì chip mờ đi và lý do hiện ở `title` — đừng để chip bấm mà không ăn. */
  disabledReason?: string
}

interface ListQuickChipsProps {
  chips: QuickChip[]
  className?: string
}

/**
 * Cụm chip bật / tắt đặt đầu thanh lọc của màn danh sách Thu mua (kh-NT2-2).
 *
 * `aria-pressed` là thứ duy nhất nói chip đang bật với trình đọc màn hình — đổi
 * kiểu nút thôi thì chỉ người nhìn được mới biết.
 */
export function ListQuickChips({ chips, className }: ListQuickChipsProps) {
  return (
    <>
      {chips.map((chip) => (
        <Button
          key={chip.label}
          type="button"
          variant={chip.active ? 'default' : 'outline'}
          size="sm"
          aria-pressed={chip.active}
          disabled={Boolean(chip.disabledReason)}
          title={chip.disabledReason}
          className={cn('h-9 shrink-0 text-xs', className)}
          onClick={chip.onToggle}
        >
          {chip.label}
        </Button>
      ))}
    </>
  )
}
