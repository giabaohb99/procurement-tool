import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { TimeInput24h } from '@/shared/ui/time-input-24h'
import { WORK_DAY_KIND } from '@/shared/constants/statuses'
import { cn } from '@/shared/utils/cn'
import { WORK_DAY_KIND_CODE, type WorkScheduleDay } from '../types/work-schedule'
import {
  WEEKDAY_LABELS,
  dayCredit,
  formatWorkdays,
  normalizeDayOnKindChange,
} from '../utils/work-schedule-week'
import { describeDayFull } from '../utils/work-schedule-week-summary'

/** Cột lưới ở khổ máy tính: Thứ · Loại ngày · Giờ làm · Nghỉ trưa · Công. Khổ hẹp: thẻ 2 cột. */
export const WEEK_ROW_GRID =
  'grid grid-cols-2 gap-x-3 gap-y-2 md:grid-cols-[2.5rem_9.5rem_12rem_12rem_minmax(0,1fr)] md:items-center'

type TimeKey = 'start_time' | 'end_time' | 'lunch_start' | 'lunch_end'

interface TimeRangeProps {
  day: WorkScheduleDay
  from: TimeKey
  to: TimeKey
  label: string
  fromLabel: string
  toLabel: string
  onChange: (next: WorkScheduleDay) => void
}

/** Cặp giờ «08:00 – 17:00» gọn trên một dòng; nhãn nhỏ chỉ hiện ở thẻ hẹp (máy tính đã có tiêu đề cột). */
function TimeRange({ day, from, to, label, fromLabel, toLabel, onChange }: TimeRangeProps) {
  const weekdayLabel = WEEKDAY_LABELS[day.weekday]
  return (
    <div className="space-y-1">
      <p className="text-xs text-muted-foreground md:hidden">{label}</p>
      <div className="flex items-center gap-1.5">
        <TimeInput24h
          aria-label={`${weekdayLabel} — ${fromLabel}`}
          value={day[from]}
          onChange={(next) => onChange({ ...day, [from]: next })}
        />
        <span aria-hidden className="text-muted-foreground">
          –
        </span>
        <TimeInput24h
          aria-label={`${weekdayLabel} — ${toLabel}`}
          value={day[to]}
          onChange={(next) => onChange({ ...day, [to]: next })}
        />
      </div>
    </div>
  )
}

interface WorkScheduleWeekEditorRowProps {
  day: WorkScheduleDay
  disabled: boolean
  onChange: (next: WorkScheduleDay) => void
}

/**
 * MỘT hàng của bảng 7 ngày. Nghỉ -> dòng chữ mờ «Nghỉ» thay cho ô giờ; nửa ngày -> chỉ
 * cặp giờ làm; Cả ngày -> thêm cặp nghỉ trưa. Xóa giá trị lúc đổi loại do
 * `normalizeDayOnKindChange` lo, để payload không mang giờ mồ côi.
 */
export function WorkScheduleWeekEditorRow({ day, disabled, onChange }: WorkScheduleWeekEditorRowProps) {
  const weekdayLabel = WEEKDAY_LABELS[day.weekday]
  const isOff = day.day_kind === WORK_DAY_KIND_CODE.OFF
  const isFull = day.day_kind === WORK_DAY_KIND_CODE.FULL
  const credit = (
    <span className={cn('text-sm tabular-nums', isOff ? 'text-muted-foreground' : 'font-medium')}>
      {formatWorkdays(dayCredit(day.day_kind))} công
    </span>
  )

  return (
    <div
      className={cn(
        WEEK_ROW_GRID,
        'rounded-md border p-3 md:rounded-none md:border-0 md:border-b md:px-4 md:py-2.5 md:last:border-b-0',
      )}
    >
      <div className="font-semibold max-md:order-1">{weekdayLabel}</div>
      <div className="max-md:order-2 max-md:text-right md:order-5">{credit}</div>

      {disabled ? (
        <ReadOnlyValue className="max-md:order-3 max-md:col-span-2 md:col-span-3">
          {describeDayFull(day)}
        </ReadOnlyValue>
      ) : (
        <>
          <div className="max-md:order-3 max-md:col-span-2 md:order-2">
            <Select
              value={String(day.day_kind)}
              onValueChange={(value) => {
                //  Radix có thể bắn chuỗi rỗng khi đồng bộ thẻ select ẩn — không phải người chọn.
                if (value === '') return
                onChange(normalizeDayOnKindChange(day, Number(value)))
              }}
            >
              <SelectTrigger className="w-full" aria-label={`${weekdayLabel} — loại ngày`}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {WORK_DAY_KIND.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {isOff ? (
            <p className="text-sm text-muted-foreground max-md:order-4 max-md:col-span-2 md:order-3 md:col-span-2">
              Nghỉ — không làm việc
            </p>
          ) : (
            <>
              <div className="max-md:order-4 max-md:col-span-2 md:order-3 md:col-span-1">
                <TimeRange
                  day={day}
                  from="start_time"
                  to="end_time"
                  label="Giờ làm"
                  fromLabel="giờ vào"
                  toLabel="giờ ra"
                  onChange={onChange}
                />
              </div>
              <div className="max-md:order-5 max-md:col-span-2 md:order-4">
                {isFull ? (
                  <TimeRange
                    day={day}
                    from="lunch_start"
                    to="lunch_end"
                    label="Nghỉ trưa"
                    fromLabel="nghỉ trưa từ"
                    toLabel="nghỉ trưa đến"
                    onChange={onChange}
                  />
                ) : (
                  <p className="text-sm text-muted-foreground max-md:hidden">Không nghỉ trưa</p>
                )}
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
