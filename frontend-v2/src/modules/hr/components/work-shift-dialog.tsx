import { Info } from 'lucide-react'
import { useRef, useState } from 'react'

import { useAuth } from '@/core/auth/use-auth'
import { usePermission } from '@/core/authorization/use-permission'
import { Skeleton } from '@/shared/ui/skeleton'
import { useWorkShiftApplyOthers } from '../hooks/use-work-shift-apply-others'
import { useWorkShiftSubmit } from '../hooks/use-work-shift-submit'
import { useEffectiveScheduleOn } from '../hooks/use-work-shifts'
import type { WorkRosterDay, WorkRosterItem } from '../types/work-roster'
import type { WorkShiftTarget } from '../types/work-shift'
import { isLeaveHeld, resolveShiftCellAccess, SHIFT_LOCK_HINT } from '../utils/work-shift-access'
import { weekdayOf } from '../utils/work-shift-date'
import { initialRangesForCell, mergeRanges, templateDayToRanges } from '../utils/work-shift-hours'
import { rangesToRows, rowsToSegments, validateShiftRows, type ShiftRow } from '../utils/work-shift-rows'
import { resolveShiftSubmit } from '../utils/work-shift-submit-state'
import { WorkShiftApplyOthers } from './work-shift-apply-others'
import { WorkShiftApplyOthersSection } from './work-shift-apply-others-section'
import { WorkShiftDialogFooter } from './work-shift-dialog-footer'
import { WorkShiftDialogHeader } from './work-shift-dialog-header'
import { WorkShiftDialogNotices } from './work-shift-dialog-notices'
import { WorkShiftErrorAlert } from './work-shift-error-alert'
import { WorkShiftHoursSection } from './work-shift-hours-section'
import { WorkShiftModal } from './work-shift-modal'
import { WorkShiftNoteField } from './work-shift-note-field'
import { WorkShiftPresetsBar } from './work-shift-presets-bar'

const ROUNDED_HINT =
  'Mẫu tuần có giờ lẻ — ca xếp theo giờ tròn nên đã làm tròn: giờ bắt đầu lùi về giờ chẵn, giờ kết thúc lên giờ chẵn.'

interface WorkShiftDialogProps {
  /** `null` = hộp đóng. */
  target: WorkShiftTarget | null
  onClose: () => void
  /** Kỳ đang xem + nhân sự trên trang — nguồn cho "Áp cho ngày khác". */
  days: WorkRosterDay[]
  items: WorkRosterItem[]
  todayISO: string
}

/**
 * HỘP XẾP CA một người một ngày (duoc-CR-761, bản đại ca chốt 16/11/2026): mục "Khung giờ làm việc" (tóm tắt giờ /
 * công, thanh 00:00–24:00, danh sách khung "Từ – Đến"), mẫu nhanh, ghi chú, mục gập "Áp cùng ca cho ngày / người
 * khác"; chân hộp Về mẫu tuần · Hủy · Lưu (hoặc "Lưu cho N ô"). Thân hộp gắn `key` theo ô nên mở ô khác là dựng lại từ
 * đầu (không cần effect đặt lại state).
 */
export function WorkShiftDialog({ target, onClose, ...rest }: WorkShiftDialogProps) {
  return (
    <WorkShiftModal open={target !== null} onClose={onClose}>
      {target && (
        <WorkShiftDialogBody key={`${target.item.employee_id}:${target.date}`} target={target} onClose={onClose} {...rest} />
      )}
    </WorkShiftModal>
  )
}

function WorkShiftDialogBody({ target, onClose, days, items, todayISO }: WorkShiftDialogProps & { target: WorkShiftTarget }) {
  const { item, date } = target
  const { user } = useAuth()
  const { can } = usePermission()
  const viewer = { employeeId: user?.employee_id }
  const cell = item.cells.find((c) => c.date === date)
  const leave = cell?.leave
  const access = resolveShiftCellAccess(can, item.employee_id, date, viewer, todayISO, isLeaveHeld(cell))
  const readOnly = !access.canWrite
  const hasShift = Boolean(cell?.is_shift && cell.shift)

  //  Mẫu tuần ĐANG ÁP ngày đó (kèm nghỉ trưa): điền sẵn khi ô chưa có ca riêng, và cho nút "Theo lịch tuần".
  const effective = useEffectiveScheduleOn(item.employee_id, date, !readOnly || !hasShift)
  const templateDay = effective.data?.days.find((d) => d.weekday === weekdayOf(date))
  const template = templateDay ? templateDayToRanges(templateDay) : null
  const prefill = initialRangesForCell(cell, templateDay)
  //  Ô chưa có ca: chờ mẫu tuần nạp xong mới bày khung (không để các dòng nhảy sau khi nạp), và không lưu được tới khi
  //  người dùng thật sự sửa gì đó — tránh bấm Lưu nhầm biến cả ngày mẫu tuần thành "ca xếp riêng".
  const templateLoading = !hasShift && effective.isPending
  const templateFailed = !hasShift && effective.isError

  const [draft, setDraft] = useState<ShiftRow[] | null>(null)
  const [roundedHint, setRoundedHint] = useState(false)
  const rows = draft ?? rangesToRows(prefill.ranges, 'p')
  const showRounded = draft === null ? !hasShift && prefill.rounded : roundedHint
  const validation = validateShiftRows(rows)
  const initialNote = cell?.shift?.note ?? ''
  const [note, setNote] = useState(initialNote)
  const dirty = draft !== null || note.trim() !== initialNote.trim()
  const others = useWorkShiftApplyOthers({ item, date, days, items, viewer, todayISO })
  const presetCounter = useRef(0)
  const nameOf = (id: number) => items.find((i) => i.employee_id === id)?.full_name
  const { pending, error, saveCell, resetToTemplate, applyBulk } = useWorkShiftSubmit({
    employeeId: item.employee_id,
    fullName: item.full_name,
    date,
    nameOf,
    onDone: onClose,
  })
  const segments = rowsToSegments(rows)
  const trimmedNote = note.trim()

  /** Mẫu nhanh thay CẢ danh sách khung; khóa dòng mới mỗi lượt để React dựng lại ô chọn. */
  const applyPreset = (ranges: readonly (readonly number[])[], rounded = false) => {
    presetCounter.current += 1
    setDraft(rangesToRows(mergeRanges(ranges), `t${presetCounter.current}-`))
    setRoundedHint(rounded)
  }

  const lockHint = access.lock ? SHIFT_LOCK_HINT[access.lock] : null
  const submit = resolveShiftSubmit({
    pending,
    templateLoading,
    rowsValid: validation.valid,
    cells: others.cells,
    bulkWarning: others.warning,
    hasShift,
    dirty,
  })
  const onSubmit = () => {
    if (!submit.enabled) return
    if (submit.bulk) void applyBulk({ employee_ids: others.employeeIds, dates: others.dates, segments, note: trimmedNote })
    else void saveCell({ segments, note: trimmedNote })
  }

  return (
    <>
      <WorkShiftDialogHeader
        fullName={item.full_name}
        date={date}
        status={!hasShift ? 'template' : cell?.shift?.is_day_off ? 'shift-off' : 'shift'}
      />

      {/*  Thân cuộn (tấm trượt điện thoại cao tối đa 90% màn), chân hộp dính đáy. */}
      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-5 py-4">
        {templateLoading ? (
          <div aria-label="Đang đọc mẫu lịch tuần" className="space-y-2">
            <Skeleton className="h-11 w-full" />
            <Skeleton className="h-9 w-full" />
            <Skeleton className="h-9 w-full" />
          </div>
        ) : (
          <>
            {templateFailed && draft === null && (
              <p role="alert" className="text-sm text-destructive">
                Không đọc được mẫu lịch tuần của ngày này — hãy tự thêm khung giờ hoặc chọn mẫu nhanh.
              </p>
            )}
            <WorkShiftHoursSection rows={rows} onChange={setDraft} validation={validation} readOnly={readOnly} />
          </>
        )}

        {showRounded && !readOnly && (
          <p className="flex items-start gap-2 text-xs text-muted-foreground">
            <Info aria-hidden className="mt-0.5 size-3.5 shrink-0" />
            {ROUNDED_HINT}
          </p>
        )}

        {!readOnly && <WorkShiftPresetsBar template={template} onApply={applyPreset} />}

        <WorkShiftNoteField value={note} onChange={setNote} readOnly={readOnly} />

        {!readOnly && (
          <WorkShiftApplyOthersSection
            open={others.open}
            onOpenChange={others.setOpen}
            extraDates={others.extraDates.size}
            extraEmployees={others.extraEmployees.size}
            cells={others.cells}
            warning={others.warning}
          >
            <WorkShiftApplyOthers
              days={others.otherDays}
              allowedDates={others.allowedDates}
              employees={others.otherEmployees}
              heldEmployeeIds={others.heldEmployeeIds}
              selectedDates={others.extraDates}
              selectedEmployees={others.extraEmployees}
              onDatesChange={others.setExtraDates}
              onEmployeesChange={others.setExtraEmployees}
            />
          </WorkShiftApplyOthersSection>
        )}

        {error && <WorkShiftErrorAlert error={error} />}
        <WorkShiftDialogNotices lockHint={lockHint} leave={leave} />
      </div>

      <WorkShiftDialogFooter
        readOnly={readOnly}
        onClose={onClose}
        showReset={hasShift && access.canDelete}
        resetBlocked={access.resetBlocked}
        onReset={() => void resetToTemplate()}
        pending={pending}
        submit={submit}
        onSubmit={onSubmit}
      />
    </>
  )
}
