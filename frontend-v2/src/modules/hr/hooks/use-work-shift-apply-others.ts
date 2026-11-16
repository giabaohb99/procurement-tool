import { useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import type { WorkRosterDay, WorkRosterItem } from '../types/work-roster'
import { isLeaveHeld, pickArrangeableDates, pickArrangeableEmployeeIds, type ShiftViewer } from '../utils/work-shift-access'
import { findLeaveHeldCells } from '../utils/work-shift-bulk-conflicts'
import { bulkLimitMessage } from '../utils/work-shift-bulk-limits'

interface ApplyOthersOptions {
  item: WorkRosterItem
  date: string
  days: readonly WorkRosterDay[]
  items: readonly WorkRosterItem[]
  viewer: ShiftViewer
  todayISO: string
}

/**
 * Trạng thái mục "Áp cùng ca cho ngày / người khác" của hộp xếp ca (duoc-CR-761): ngày / người chọn thêm, trần một lượt, và các ô
 * đang bị đơn nghỉ giữ (backend từ chối CẢ lượt nếu có) để chặn trước kèm câu báo.
 */
export function useWorkShiftApplyOthers({ item, date, days, items, viewer, todayISO }: ApplyOthersOptions) {
  const { can } = usePermission()
  const [open, setOpen] = useState(false)
  const [extraDates, setExtraDates] = useState<Set<string>>(new Set())
  const [extraEmployees, setExtraEmployees] = useState<Set<number>>(new Set())

  const otherDays = days.filter((d) => d.date !== date)
  //  Ngày người đang mở đã có đơn nghỉ thì không chọn được — người đó luôn nằm trong lượt áp.
  const ownCells = new Map(item.cells.map((c) => [c.date, c]))
  const allowedDates = new Set(
    pickArrangeableDates(can, otherDays.map((d) => d.date), todayISO).filter((d) => !isLeaveHeld(ownCells.get(d))),
  )
  const arrangeable = new Set(pickArrangeableEmployeeIds(can, items.map((i) => i.employee_id), viewer))
  const otherEmployees = items.filter((i) => i.employee_id !== item.employee_id && arrangeable.has(i.employee_id))

  const employeeIds = [item.employee_id, ...extraEmployees]
  const dates = [date, ...extraDates]
  const cells = employeeIds.length * dates.length
  const held = findLeaveHeldCells(items, employeeIds, dates)
  //  Người khác có đơn nghỉ ở BẤT KỲ ngày đang chọn → đánh dấu trong danh sách để bỏ chọn cho nhanh.
  const heldEmployeeIds = new Set(findLeaveHeldCells(otherEmployees, otherEmployees.map((e) => e.employee_id), dates).map((c) => c.employeeId))
  const limit = bulkLimitMessage(employeeIds.length, dates.length)
  const warning =
    limit ?? (held.length > 0 ? `${held.length} ô đã có đơn nghỉ — bỏ chọn người / ngày đó rồi mới áp được.` : null)

  return {
    /** Mục gập "Áp cùng ca" đang mở; gập lại KHÔNG bỏ lựa chọn (dòng tóm tắt vẫn hiện, nút Lưu vẫn là "Lưu cho N ô"). */
    open,
    setOpen,
    otherDays,
    allowedDates,
    otherEmployees,
    heldEmployeeIds,
    extraDates,
    setExtraDates,
    extraEmployees,
    setExtraEmployees,
    employeeIds,
    dates,
    cells,
    /** Câu chặn lượt áp (vượt trần / có ô bị đơn nghỉ giữ); `null` = áp được. */
    warning,
  }
}
