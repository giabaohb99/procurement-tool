import { Copy } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { WEEK_PRESETS, type WeekPresetKey } from '../utils/work-schedule-week'

interface WorkScheduleWeekQuickActionsProps {
  onPreset: (preset: WeekPresetKey) => void
  onCopyMonday: () => void
}

/**
 * Hàng thao tác nhanh đầu bảng 7 ngày. `type="button"` bắt buộc: các nút nằm trong
 * <form>, mặc định là submit và bấm một cái là lưu cả mẫu.
 */
export function WorkScheduleWeekQuickActions({ onPreset, onCopyMonday }: WorkScheduleWeekQuickActionsProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-xs font-medium text-muted-foreground">Điền nhanh:</span>
      {WEEK_PRESETS.map((preset) => (
        <Button key={preset.key} type="button" variant="outline" size="sm" onClick={() => onPreset(preset.key)}>
          {preset.label}
        </Button>
      ))}
      <Button type="button" variant="ghost" size="sm" onClick={onCopyMonday}>
        <Copy />
        Áp giờ T2 cho T3–T6
      </Button>
    </div>
  )
}
