import { useMemo, type CSSProperties } from 'react'

import { Checkbox } from '@/shared/ui/checkbox'
import { cn } from '@/shared/utils/cn'
import type { WorkRosterDay, WorkRosterInteraction, WorkRosterItem } from '../types/work-roster'
import { indexCellsByDate } from '../utils/work-roster-cell'
import { isLeaveHeld, SHIFT_LOCK_HINT } from '../utils/work-shift-access'
import { WorkRosterCellView } from './work-roster-cell-view'
import { ROSTER_ROW_GRID, STICKY_NAME_CELL } from './work-roster-grid-layout'

interface WorkRosterRowProps {
  item: WorkRosterItem
  days: WorkRosterDay[]
  compact: boolean
  todayISO: string
  /** Hàng có nghỉ phép: dính trong đợt của nó — `top`/`marginBottom` do `WorkRosterGridBody` tính. */
  stickyStyle?: CSSProperties
  interaction?: WorkRosterInteraction
}

/**
 * Một hàng nhân sự. Hàng có nghỉ phép dính (`sticky`, nền đặc, z-15: trên hàng thường đang trôi qua, dưới đầu
 * bảng z-30 để khi bị đẩy thì chui vào dưới đầu bảng). Hôm nay chỉ phủ một lớp nền rất nhạt lên cả cột.
 */
export function WorkRosterRow({ item, days, compact, todayISO, stickyStyle, interaction }: WorkRosterRowProps) {
  const cells = useMemo(() => indexCellsByDate(item), [item])
  const sticky = stickyStyle !== undefined
  const selection = interaction?.selection
  const onEditCell = interaction?.onEditCell
  const selectable = selection?.canSelect(item.employee_id) ?? false
  return (
    <div
      role="row"
      data-leave-row={sticky ? '' : undefined}
      style={stickyStyle}
      className={cn(ROSTER_ROW_GRID, 'border-b border-border/40', compact ? 'h-8' : 'h-10', sticky && 'sticky z-15 bg-card')}
    >
      <div role="rowheader" className={cn(STICKY_NAME_CELL, 'flex items-center gap-2 px-3')}>
        {selection && (
          //  Ô chọn dòng cho Chép tuần trước. Dòng không chọn được (Trưởng phòng — chính mình) vẫn giữ chỗ để tên thẳng hàng.
          <Checkbox
            aria-label={`Chọn ${item.full_name}`}
            checked={selectable && selection.selectedIds.has(item.employee_id)}
            disabled={!selectable}
            onCheckedChange={() => selection.onToggle(item.employee_id)}
            className={cn(!selectable && 'invisible')}
          />
        )}
        {/* Mã NV xuống dòng dưới: đứng cùng dòng thì mã ăn chỗ, tên dài bị cắt ("Nguyễn Hoàng …"). */}
        <div className="flex min-w-0 flex-col leading-tight">
          <span className="truncate text-sm font-medium" title={`${item.full_name} · ${item.code}`}>
            {item.full_name}
          </span>
          <span className={cn('truncate text-[11px] text-muted-foreground', compact && 'hidden')}>{item.code}</span>
        </div>
      </div>
      {days.map((day) => {
        const cell = cells.get(day.date)
        //  Ô đã có đơn nghỉ không xếp ca được (backend 409) — giữ link sang đơn, tooltip nói lý do.
        const leaveBlocked = onEditCell !== undefined && isLeaveHeld(cell)
        return (
          <div key={day.date} role="cell" className={cn('min-w-0 border-r border-border/40', day.date === todayISO && 'bg-primary/5')}>
            <WorkRosterCellView
              cell={cell}
              compact={compact}
              label={`${item.full_name} · ${day.date}`}
              hint={leaveBlocked ? SHIFT_LOCK_HINT.leave.replace(/\.$/, '') : undefined}
              onEdit={onEditCell && !leaveBlocked ? () => onEditCell(item, day.date) : undefined}
            />
          </div>
        )
      })}
    </div>
  )
}
