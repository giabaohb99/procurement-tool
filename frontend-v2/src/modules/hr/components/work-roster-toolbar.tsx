import { ChevronLeft, ChevronRight } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import { WORK_ROSTER_MODES, type WorkRosterMode } from '../utils/work-roster-range'

interface WorkRosterToolbarProps {
  mode: WorkRosterMode
  onModeChange: (mode: WorkRosterMode) => void
  label: string
  onShift: (step: number) => void
  onToday: () => void
}

const MODE_LABEL: Record<WorkRosterMode, string> = { week: 'Tuần', month: 'Tháng' }

/**
 * Hàng điều hướng của «Xem lịch»: Tuần/Tháng · ‹ Hôm nay › · nhãn kỳ.
 * Bộ lọc và ô tìm nằm ở `WorkRosterFilterBar` — hai việc khác nhau ("xem kỳ nào"
 * và "xem ai"), tách để mỗi bên đủ chỗ trên khổ hẹp.
 */
export function WorkRosterToolbar({ mode, onModeChange, label, onShift, onToday }: WorkRosterToolbarProps) {
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
      <div role="group" aria-label="Chế độ xem lịch" className="flex items-center rounded-md border p-0.5">
        {WORK_ROSTER_MODES.map((m) => (
          <button
            key={m}
            type="button"
            aria-pressed={mode === m}
            onClick={() => onModeChange(m)}
            className={cn(
              'rounded-sm px-3 py-1 text-sm font-medium transition-colors',
              mode === m
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-accent hover:text-foreground',
            )}
          >
            {MODE_LABEL[m]}
          </button>
        ))}
      </div>

      <div className="flex items-center rounded-md border">
        <Button variant="ghost" size="icon-sm" className="rounded-r-none" aria-label="Lùi lại" onClick={() => onShift(-1)}>
          <ChevronLeft className="size-4" />
        </Button>
        <Button variant="ghost" size="sm" className="rounded-none border-x px-3" onClick={onToday}>
          Hôm nay
        </Button>
        <Button variant="ghost" size="icon-sm" className="rounded-l-none" aria-label="Tiến tới" onClick={() => onShift(1)}>
          <ChevronRight className="size-4" />
        </Button>
      </div>

      <span aria-live="polite" className="text-base font-semibold tabular-nums">
        {label}
      </span>
    </div>
  )
}
