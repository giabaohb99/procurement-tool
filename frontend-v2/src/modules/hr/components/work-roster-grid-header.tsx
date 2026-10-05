import { cn } from '@/shared/utils/cn'
import type { WorkRosterDay } from '../types/work-roster'
import { WEEKDAY_LABELS } from '../utils/calendar-grid'
import type { WorkRosterMode } from '../utils/work-roster-range'
import { ROSTER_ROW_GRID, STICKY_NAME_CELL } from './work-roster-grid-layout'

export interface WorkRosterColumnInfo {
  date: string
  closed: boolean
  working: number
  off: number
}

interface WorkRosterGridHeaderProps {
  days: WorkRosterDay[]
  columns: WorkRosterColumnInfo[]
  mode: WorkRosterMode
  todayISO: string
}

/** `2026-10-05` → `5/10` (tuần) hoặc `5` (tháng: cột hẹp). */
function dayLabel(iso: string, mode: WorkRosterMode): string {
  const [, m, d] = iso.split('-').map(Number)
  return mode === 'week' ? `${d}/${m}` : `${d}`
}

/**
 * Đầu bảng = MỘT khối dính `top-0` gồm hàng ngày (h-12) + hàng tổng «Nghỉ (trang này)» (h-7). Chiều cao cố
 * định nên mép dưới luôn là `ROSTER_HEADER_HEIGHT` — chồng dính hàng có nghỉ bám vào đó, không phải đo.
 */
export function WorkRosterGridHeader({ days, columns, mode, todayISO }: WorkRosterGridHeaderProps) {
  const compact = mode === 'month'
  return (
    <div role="rowgroup" className="sticky top-0 z-30 bg-card">
      <div role="row" className={cn(ROSTER_ROW_GRID, 'h-12 border-b')}>
        <div role="columnheader" className={cn(STICKY_NAME_CELL, 'flex items-center px-3 text-xs font-medium text-muted-foreground')}>
          Nhân sự
        </div>
        {days.map((day, i) => {
          const isToday = day.date === todayISO
          return (
            <div
              key={day.date}
              role="columnheader"
              title={day.holiday_name || undefined}
              aria-current={isToday ? 'date' : undefined}
              className={cn(
                'flex flex-col items-center justify-center border-t-2 border-r border-t-transparent border-r-border/40 text-center text-xs leading-tight',
                columns[i]?.closed && 'bg-muted text-muted-foreground/70',
                day.holiday_name && 'bg-destructive/10 text-destructive',
                isToday && 'border-t-primary bg-primary/10 font-semibold text-primary',
              )}
            >
              <span className={cn('text-[10px] uppercase', !isToday && !day.holiday_name && 'text-muted-foreground')}>
                {WEEKDAY_LABELS[day.weekday] ?? ''}
              </span>
              <span className="text-sm font-medium tabular-nums">{dayLabel(day.date, mode)}</span>
              {!compact && day.holiday_name && (
                <span className="max-w-full truncate px-1 text-[10px] font-normal">{day.holiday_name}</span>
              )}
            </div>
          )
        })}
      </div>
      <div role="row" className={cn(ROSTER_ROW_GRID, 'h-7 border-b')}>
        <div role="rowheader" className={cn(STICKY_NAME_CELL, 'flex items-center px-3 text-xs font-medium text-muted-foreground')}>
          Nghỉ (trang này)
        </div>
        {columns.map((t) => (
          <div
            key={t.date}
            role="cell"
            title={`Đang làm ${t.working} · Nghỉ ${t.off}`}
            className="flex items-center justify-center border-r border-border/40 px-0.5"
          >
            {/* Số liệu đầy đủ cho trình đọc màn hình — viên thuốc chỉ là phần nhìn và ẩn khi cả cột nghỉ. */}
            <span className="sr-only">{`Đi làm ${t.working}, nghỉ ${t.off}`}</span>
            {t.off > 0 && !t.closed && (
              <span aria-hidden className="inline-flex min-w-5 items-center justify-center rounded-full bg-info/15 px-1.5 text-[11px] font-semibold leading-5 text-info tabular-nums">
                {t.off}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
