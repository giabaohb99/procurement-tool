import type { ShiftRow, ShiftRowsValidation } from '../utils/work-shift-rows'
import { WorkShiftDayBar } from './work-shift-day-bar'
import { WorkShiftSegmentRows } from './work-shift-segment-rows'
import { WorkShiftTotalStats } from './work-shift-total-stats'

interface WorkShiftHoursSectionProps {
  rows: ShiftRow[]
  onChange: (next: ShiftRow[]) => void
  validation: ShiftRowsValidation
  readOnly: boolean
}

/**
 * Mục "Khung giờ làm việc" của hộp xếp ca (duoc-CR-761): hàng tiêu đề (trái tên mục, phải tóm tắt "8 giờ · 1 ngày
 * công"), thanh ngày 00:00–24:00 có số khung, rồi danh sách khung. Tóm tắt nằm ngay trên đầu thay cho dòng tổng rời
 * phía dưới của bản trước.
 */
export function WorkShiftHoursSection({ rows, onChange, validation, readOnly }: WorkShiftHoursSectionProps) {
  return (
    <section aria-labelledby="work-shift-hours-title" className="space-y-3">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <h3 id="work-shift-hours-title" className="text-sm font-medium">
          Khung giờ làm việc
        </h3>
        <WorkShiftTotalStats rows={rows} hasRowErrors={Object.keys(validation.rowErrors).length > 0} />
      </div>
      <WorkShiftDayBar segments={rows.map((r) => ({ ...r, invalid: Boolean(validation.rowErrors[r.id]) }))} />
      <WorkShiftSegmentRows rows={rows} onChange={onChange} validation={validation} readOnly={readOnly} />
    </section>
  )
}
