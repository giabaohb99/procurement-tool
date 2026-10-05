import { useMemo } from 'react'
import { useController, type Control } from 'react-hook-form'

import type { CrudRecord } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'
import { cn } from '@/shared/utils/cn'
import { WEEK_ROW_GRID, WorkScheduleWeekEditorRow } from './work-schedule-week-editor-row'
import { WorkScheduleWeekQuickActions } from './work-schedule-week-quick-actions'
import {
  applyWeekPreset,
  copyMondayToWeekdays,
  fillWeek,
  formatWorkdays,
  sumWeeklyWorkdays,
} from '../utils/work-schedule-week'
import { validateWeekDays } from '../utils/work-schedule-validation'

interface WorkScheduleWeekEditorProps {
  control: Control<CrudRecord>
  /** Tên ô trong form (`days`) — component tự nối vào bằng `useController`. */
  name: string
  disabled?: boolean
  className?: string
}

/**
 * Khối «Lịch 7 ngày» của MẪU LỊCH TUẦN: tiêu đề + tổng công + thao tác nhanh ở đầu,
 * rồi bảy hàng. Không giữ state riêng: giá trị nằm trong react-hook-form và mỗi lần sửa
 * phát lại cả mảng 7 hàng đã chuẩn hóa — thiếu thứ nào (dữ liệu lỗi) thì hàng đó hiện
 * «Nghỉ» và được gửi lên đủ. Giờ luôn hiện 24h «HH:MM» (xem `TimeInput24h`).
 */
export function WorkScheduleWeekEditor({
  control,
  name,
  disabled = false,
  className,
}: WorkScheduleWeekEditorProps) {
  const { field, fieldState } = useController({
    control,
    name,
    rules: { validate: validateWeekDays },
  })
  const week = useMemo(() => fillWeek(field.value), [field.value])
  const total = sumWeeklyWorkdays(week)

  return (
    <section className={cn('space-y-3', className)} aria-label="Lịch 7 ngày trong tuần">
      <div className="flex flex-wrap items-center justify-between gap-2">
        {disabled ? (
          <span />
        ) : (
          <WorkScheduleWeekQuickActions
            onPreset={(preset) => field.onChange(applyWeekPreset(week, preset))}
            onCopyMonday={() => field.onChange(copyMondayToWeekdays(week))}
          />
        )}
        <Badge variant="secondary" className="text-sm">
          Tổng: {formatWorkdays(total)} ngày công/tuần
        </Badge>
      </div>

      <div className="rounded-lg md:border">
        <div
          className={cn(
            WEEK_ROW_GRID,
            'border-b bg-muted/40 px-4 py-2 text-xs font-medium text-muted-foreground max-md:hidden',
          )}
        >
          <span>Thứ</span>
          <span>Loại ngày</span>
          <span>Giờ làm</span>
          <span>Nghỉ trưa</span>
          <span>Công</span>
        </div>
        <div className="space-y-2 md:space-y-0">
          {week.map((day, index) => (
            <WorkScheduleWeekEditorRow
              key={day.weekday}
              day={day}
              disabled={disabled}
              onChange={(next) => field.onChange(week.map((d, k) => (k === index ? next : d)))}
            />
          ))}
        </div>
      </div>

      {fieldState.error?.message && (
        <p role="alert" className="text-sm text-destructive">
          {fieldState.error.message}
        </p>
      )}
    </section>
  )
}
