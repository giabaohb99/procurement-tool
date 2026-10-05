import { useMemo, type CSSProperties } from 'react'

import { cn } from '@/shared/utils/cn'
import type { WorkRosterDay, WorkRosterItem } from '../types/work-roster'
import { indexCellsByDate } from '../utils/work-roster-cell'
import { WorkRosterCellView } from './work-roster-cell-view'
import { ROSTER_ROW_GRID, STICKY_NAME_CELL } from './work-roster-grid-layout'

interface WorkRosterRowProps {
  item: WorkRosterItem
  days: WorkRosterDay[]
  compact: boolean
  todayISO: string
  /** Hàng có nghỉ phép: dính trong đợt của nó — `top`/`marginBottom` do `WorkRosterGridBody` tính. */
  stickyStyle?: CSSProperties
}

/**
 * Một hàng nhân sự. Hàng có nghỉ phép dính (`sticky`, nền đặc, z-15: trên hàng thường đang trôi qua, dưới đầu
 * bảng z-30 để khi bị đẩy thì chui vào dưới đầu bảng). Hôm nay chỉ phủ một lớp nền rất nhạt lên cả cột.
 */
export function WorkRosterRow({ item, days, compact, todayISO, stickyStyle }: WorkRosterRowProps) {
  const cells = useMemo(() => indexCellsByDate(item), [item])
  const sticky = stickyStyle !== undefined
  return (
    <div
      role="row"
      data-leave-row={sticky ? '' : undefined}
      style={stickyStyle}
      className={cn(ROSTER_ROW_GRID, 'border-b border-border/40', compact ? 'h-8' : 'h-10', sticky && 'sticky z-15 bg-card')}
    >
      <div role="rowheader" className={cn(STICKY_NAME_CELL, 'flex items-center px-3')}>
        {/* Mã NV xuống dòng dưới: đứng cùng dòng thì mã ăn chỗ, tên dài bị cắt («Nguyễn Hoàng …»). */}
        <div className="flex min-w-0 flex-col leading-tight">
          <span className="truncate text-sm font-medium" title={`${item.full_name} · ${item.code}`}>
            {item.full_name}
          </span>
          <span className={cn('truncate text-[11px] text-muted-foreground', compact && 'hidden')}>{item.code}</span>
        </div>
      </div>
      {days.map((day) => (
        <div key={day.date} role="cell" className={cn('min-w-0 border-r border-border/40', day.date === todayISO && 'bg-primary/5')}>
          <WorkRosterCellView cell={cells.get(day.date)} compact={compact} label={`${item.full_name} · ${day.date}`} />
        </div>
      ))}
    </div>
  )
}
