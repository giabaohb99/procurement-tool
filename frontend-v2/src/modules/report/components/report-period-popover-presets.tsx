import { Check } from 'lucide-react'

import { cn } from '@/shared/utils/cn'

import { REPORT_PRESETS, type ReportPresetKey } from '../config/report-period-presets'

interface ReportPeriodPopoverPresetsProps {
  value: ReportPresetKey
  onSelect: (preset: ReportPresetKey) => void
}

/**
 * Cột TRÁI của popover kỳ (`ReportPeriodControl`) — danh sách dọc 9 preset cố
 * định + "Tùy chọn khoảng ngày" (`REPORT_PRESETS`, đủ 10 mục). Bấm một mục chỉ
 * đổi bản NHÁP; chưa ghi lên URL cho tới khi bấm "Áp dụng" ở popover cha.
 */
export function ReportPeriodPopoverPresets({ value, onSelect }: ReportPeriodPopoverPresetsProps) {
  return (
    <ul className="flex shrink-0 flex-row gap-0.5 overflow-x-auto p-2 sm:w-44 sm:flex-col sm:overflow-visible sm:border-r">
      {REPORT_PRESETS.map((option) => {
        const active = option.key === value
        return (
          <li key={option.key} className="shrink-0">
            <button
              type="button"
              onClick={() => onSelect(option.key)}
              aria-pressed={active}
              className={cn(
                'flex w-full items-center justify-between gap-2 rounded-md px-2.5 py-1.5 text-left text-sm whitespace-nowrap transition-colors hover:bg-accent',
                active && 'bg-accent font-medium text-accent-foreground',
              )}
            >
              {option.label}
              {active && <Check className="size-4 shrink-0" aria-hidden />}
            </button>
          </li>
        )
      })}
    </ul>
  )
}
