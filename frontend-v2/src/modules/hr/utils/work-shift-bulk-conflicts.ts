import type { WorkRosterItem } from '../types/work-roster'
import { isLeaveHeld } from './work-shift-access'

/**
 * Ô (người × ngày) của một lượt "Áp cho ngày khác" đang bị đơn nghỉ giữ ngày (duoc-CR-761). Backend từ chối CẢ lượt nếu
 * có dù một ô như vậy (409 `leave_conflict`), nên hộp xếp ca báo trước và chặn nút Áp. Chỉ biết được người / ngày có
 * trên trang đang xem.
 */
export function findLeaveHeldCells(
  items: readonly WorkRosterItem[],
  employeeIds: readonly number[],
  dates: readonly string[],
): { employeeId: number; date: string }[] {
  const wanted = new Set(employeeIds)
  const out: { employeeId: number; date: string }[] = []
  for (const item of items) {
    if (!wanted.has(item.employee_id)) continue
    for (const date of dates) {
      if (isLeaveHeld(item.cells.find((c) => c.date === date))) out.push({ employeeId: item.employee_id, date })
    }
  }
  return out
}
