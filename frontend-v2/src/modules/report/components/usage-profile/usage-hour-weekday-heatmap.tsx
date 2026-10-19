import { cn } from '@/shared/utils/cn'

import { heatLevel } from '../../utils/usage-profile-helpers'

const WEEKDAYS = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']

interface UsageHourWeekdayHeatmapProps {
  /** 7 hàng (thứ Hai đầu) × 24 cột (giờ VN) — số lượt thao tác. */
  grid: number[][]
}

const LEVEL_CLASS = ['bg-muted', 'bg-primary/20', 'bg-primary/40', 'bg-primary/65', 'bg-primary']

/** Lưới CSS 7×24 — tự dựng vì chỉ là các ô tô màu, không cần thư viện biểu đồ. */
export function UsageHourWeekdayHeatmap({ grid }: UsageHourWeekdayHeatmapProps) {
  const max = Math.max(0, ...grid.flat())
  if (max === 0) return <p className="text-sm text-muted-foreground">Chưa có lượt thao tác nào trong kỳ.</p>
  return (
    <div className="overflow-x-auto" role="img" aria-label="Bản đồ nhiệt thao tác theo giờ và thứ">
      <div className="inline-grid min-w-[560px] grid-cols-[2rem_repeat(24,minmax(0,1fr))] gap-0.5 text-[10px]">
        <span />
        {Array.from({ length: 24 }, (_, h) => (
          <span key={h} className="text-center text-muted-foreground">
            {h % 3 === 0 ? h : ''}
          </span>
        ))}
        {WEEKDAYS.map((day, d) => (
          <div key={day} className="contents">
            <span className="pr-1 text-right leading-5 text-muted-foreground">{day}</span>
            {Array.from({ length: 24 }, (_, h) => {
              const value = grid[d]?.[h] ?? 0
              return (
                <span
                  key={h}
                  title={`${day} ${String(h).padStart(2, '0')}h: ${value} lượt`}
                  className={cn('h-5 rounded-sm', LEVEL_CLASS[heatLevel(value, max)])}
                />
              )
            })}
          </div>
        ))}
      </div>
    </div>
  )
}
