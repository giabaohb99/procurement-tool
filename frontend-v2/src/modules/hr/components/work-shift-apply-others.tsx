import type { Dispatch, SetStateAction } from 'react'

import { Checkbox } from '@/shared/ui/checkbox'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import type { WorkRosterDay, WorkRosterItem } from '../types/work-roster'
import { WEEKDAY_LABELS } from '../utils/calendar-grid'

interface WorkShiftApplyOthersProps {
  /** Các ngày của kỳ đang xem, TRỪ ngày đang mở. */
  days: WorkRosterDay[]
  /** Ngày người xem ghi được (Trưởng phòng: từ hôm nay). Ngày ngoài danh sách vẫn hiện nhưng không chọn được. */
  allowedDates: ReadonlySet<string>
  /** Nhân sự trên trang người xem ghi được, TRỪ người đang mở. */
  employees: WorkRosterItem[]
  /** Người có đơn nghỉ ở một trong các ngày đang chọn — gắn nhãn để bỏ chọn. */
  heldEmployeeIds: ReadonlySet<number>
  selectedDates: ReadonlySet<string>
  selectedEmployees: ReadonlySet<number>
  //  Dispatcher của `useState` để bật / tắt bằng HÀM CẬP NHẬT: hai cú bấm trong cùng một nhịp không đè nhau
  //  (bản đầu truyền thẳng tập mới → bấm nhanh hai ngày chỉ giữ lại ngày sau).
  onDatesChange: Dispatch<SetStateAction<Set<string>>>
  onEmployeesChange: Dispatch<SetStateAction<Set<number>>>
}

function toggle<T>(set: ReadonlySet<T>, value: T): Set<T> {
  const next = new Set(set)
  if (next.has(value)) next.delete(value)
  else next.add(value)
  return next
}

/** "2026-11-17" → "17/11". */
function shortDate(iso: string): string {
  return `${Number(iso.slice(8, 10))}/${Number(iso.slice(5, 7))}`
}

/**
 * Thân phần "Áp cùng ca cho ngày / người khác" của hộp xếp ca (khung gập ở `work-shift-apply-others-section.tsx`
 * bày tiêu đề, dòng tóm tắt và câu chặn): chọn thêm ngày trong kỳ đang xem và / hoặc thêm người trên trang. Bộ khung
 * đang chọn sẽ áp cho MỌI tổ hợp (người × ngày), kể cả ô đang mở — đúng hợp đồng `/bulk` (sai một ô là không ghi ô nào).
 */
export function WorkShiftApplyOthers({
  days,
  allowedDates,
  employees,
  heldEmployeeIds,
  selectedDates,
  selectedEmployees,
  onDatesChange,
  onEmployeesChange,
}: WorkShiftApplyOthersProps) {
  const selectableDays = days.filter((d) => allowedDates.has(d.date))
  return (
    <div className="space-y-3 rounded-md border bg-muted/30 p-3">
      <section aria-label="Thêm ngày" className="space-y-1.5">
        <div className="flex items-center justify-between gap-2">
          <h3 className="text-sm font-medium">Thêm ngày</h3>
          <div className="flex gap-1">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-xs"
              disabled={selectableDays.length === 0}
              onClick={() => onDatesChange(new Set(selectableDays.map((d) => d.date)))}
            >
              Chọn hết
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-xs"
              disabled={selectedDates.size === 0}
              onClick={() => onDatesChange(new Set())}
            >
              Bỏ chọn
            </Button>
          </div>
        </div>
        {days.length === 0 ? (
          <p className="text-xs text-muted-foreground">Kỳ đang xem không còn ngày nào khác.</p>
        ) : (
          <div className="flex flex-wrap gap-1">
            {days.map((day) => {
              const allowed = allowedDates.has(day.date)
              const on = selectedDates.has(day.date)
              return (
                <button
                  key={day.date}
                  type="button"
                  aria-pressed={on}
                  disabled={!allowed}
                  title={allowed ? undefined : 'Không xếp được ngày này (đã qua hoặc đã có đơn nghỉ)'}
                  onClick={() => onDatesChange((prev) => toggle(prev, day.date))}
                  className={cn(
                    'flex min-w-11 flex-col items-center rounded-md border px-2 py-1 text-xs tabular-nums',
                    on ? 'border-shift bg-shift text-shift-foreground' : 'bg-card',
                    !allowed && 'cursor-not-allowed opacity-40',
                  )}
                >
                  <span>{WEEKDAY_LABELS[day.weekday] ?? ''}</span>
                  <span className="font-semibold">{shortDate(day.date)}</span>
                </button>
              )
            })}
          </div>
        )}
      </section>

      <section aria-label="Thêm người" className="space-y-1.5">
        <div className="flex items-center justify-between gap-2">
          <h3 className="text-sm font-medium">Thêm người (trên trang này)</h3>
          <div className="flex gap-1">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-xs"
              disabled={employees.length === 0}
              onClick={() => onEmployeesChange(new Set(employees.map((e) => e.employee_id)))}
            >
              Chọn hết
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-xs"
              disabled={selectedEmployees.size === 0}
              onClick={() => onEmployeesChange(new Set())}
            >
              Bỏ chọn
            </Button>
          </div>
        </div>
        {employees.length === 0 ? (
          <p className="text-xs text-muted-foreground">Không còn ai khác trên trang này để xếp cùng.</p>
        ) : (
          <ul className="max-h-40 space-y-0.5 overflow-y-auto rounded-md border bg-card p-1">
            {employees.map((emp) => (
              <li key={emp.employee_id}>
                <label className="flex cursor-pointer items-center gap-2 rounded-sm px-2 py-1 text-sm hover:bg-accent">
                  <Checkbox
                    checked={selectedEmployees.has(emp.employee_id)}
                    onCheckedChange={() => onEmployeesChange((prev) => toggle(prev, emp.employee_id))}
                  />
                  <span className="min-w-0 flex-1 truncate">{emp.full_name}</span>
                  {heldEmployeeIds.has(emp.employee_id) && (
                    <span className="shrink-0 rounded-sm bg-leave-approved px-1.5 text-[11px] text-leave-approved-foreground">
                      Có đơn nghỉ
                    </span>
                  )}
                  <span className="shrink-0 text-xs text-muted-foreground">{emp.code}</span>
                </label>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
