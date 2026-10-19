import type { UsageDailyRow } from '../../types/usage-profile'
import { classifyDay, type DayKind } from '../../utils/usage-profile-helpers'
import { cn } from '@/shared/utils/cn'

const KIND_META: Record<DayKind, { label: string; className: string }> = {
  worked: { label: 'Đi làm', className: 'bg-emerald-500' },
  leave: { label: 'Nghỉ phép', className: 'bg-sky-400' },
  holiday: { label: 'Lễ', className: 'bg-violet-400' },
  absent: { label: 'Không vào', className: 'bg-rose-400' },
  off: { label: 'Ngày nghỉ', className: 'bg-muted' },
}

/** Dải ngày: mỗi ô một ngày, màu theo loại; chú giải bên dưới. */
export function UsageDayStrip({ days }: { days: UsageDailyRow[] }) {
  if (days.length === 0) return <p className="text-sm text-muted-foreground">Chưa có số liệu theo ngày.</p>
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-0.5">
        {days.map((day) => {
          const kind = classifyDay(day)
          return (
            <span
              key={day.day}
              title={`${day.day}: ${KIND_META[kind].label}`}
              className={cn('size-3.5 rounded-sm', KIND_META[kind].className)}
            />
          )
        })}
      </div>
      <ul className="flex flex-wrap gap-3 text-xs text-muted-foreground">
        {(Object.keys(KIND_META) as DayKind[]).map((kind) => (
          <li key={kind} className="flex items-center gap-1">
            <span className={cn('size-2.5 rounded-sm', KIND_META[kind].className)} />
            {KIND_META[kind].label}
          </li>
        ))}
      </ul>
    </div>
  )
}
