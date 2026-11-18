import { cn } from '@/shared/utils/cn'

import { WORK_OVERVIEW_PERIODS } from '../hooks/use-work-overview'

/** Nút gạt kỳ của các chỉ số "trong kỳ" (xong, đúng hạn, việc mới, giờ thực tế) — dùng ở màn Tổng quan Dự án và tab Báo cáo của từng dự án (duoc-CR-782). */
export function WorkOverviewPeriodSwitch({ value, onChange }: { value: number; onChange: (days: number) => void }) {
  return (
    <div role="group" aria-label="Kỳ thống kê" className="inline-flex rounded-lg border bg-background p-0.5">
      {WORK_OVERVIEW_PERIODS.map((days) => (
        <button
          key={days}
          type="button"
          aria-pressed={value === days}
          onClick={() => onChange(days)}
          className={cn(
            'rounded-md px-3 py-1 text-sm transition-colors',
            value === days ? 'bg-primary/10 font-medium text-primary' : 'text-muted-foreground hover:text-foreground',
          )}
        >
          {days} ngày
        </button>
      ))}
    </div>
  )
}
