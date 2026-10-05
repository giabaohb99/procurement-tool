import type { WorkRosterCell, WorkRosterDay, WorkRosterItem } from '../types/work-roster'
import { describeRosterCell } from './work-roster-cell'

/**
 * Hàng tổng đầu bảng: «Đang làm x / Nghỉ y» của MỘT ngày, tính trên các hàng đang xem.
 * Nhận sẵn bản đồ ngày → ô của từng hàng (`indexCellsByDate`) để tra O(1), không `find` lại.
 * «Nghỉ» gồm người nghỉ phép cả ngày + nghỉ theo lịch + ngày lễ.
 */
export function summarizeRosterDay(
  cellMaps: readonly ReadonlyMap<string, WorkRosterCell>[],
  date: string,
): { working: number; off: number } {
  let working = 0
  let off = 0
  for (const cells of cellMaps) {
    const view = describeRosterCell(cells.get(date))
    if (view.state === 'unknown') continue
    if (view.isWorking) working += 1
    else off += 1
  }
  return { working, off }
}

export interface WorkRosterDepartmentGroup {
  key: string
  departmentName: string
  items: WorkRosterItem[]
}

/**
 * Gom hàng theo phòng ban, giữ nguyên thứ tự backend trả (đã xếp phòng ban rồi tên).
 * Khóa là `department_id` — `0` là giá trị thật (nhân sự chưa có phòng ban), không
 * được coi như «không có».
 */
export function groupByDepartment(items: readonly WorkRosterItem[]): WorkRosterDepartmentGroup[] {
  const groups = new Map<number, WorkRosterDepartmentGroup>()
  for (const item of items) {
    let group = groups.get(item.department_id)
    if (!group) {
      group = {
        key: `dept-${item.department_id}`,
        departmentName: item.department_name.trim() || 'Chưa có phòng ban',
        items: [],
      }
      groups.set(item.department_id, group)
    }
    group.items.push(item)
  }
  return [...groups.values()]
}

/**
 * id những người có ÍT NHẤT một ô nghỉ phép (cả ngày / nửa buổi, đã duyệt hay chờ duyệt) trong kỳ — các
 * hàng này vào chồng dính 3 ô dưới đầu bảng khi cuộn qua (`useStickyLeaveStack`).
 * Dùng cùng `describeRosterCell` với lưới: đơn rơi vào ngày lễ / nghỉ tuần (ô không tô màu) không tính.
 */
export function pickLeaveRowIds(
  items: readonly WorkRosterItem[],
  cellMaps: readonly ReadonlyMap<string, WorkRosterCell>[],
  days: readonly Pick<WorkRosterDay, 'date'>[],
): Set<number> {
  const ids = new Set<number>()
  items.forEach((item, order) => {
    const cells = cellMaps[order]
    const hasLeave = days.some((d) => {
      const state = describeRosterCell(cells?.get(d.date)).state
      return state === 'leave' || state === 'partial'
    })
    if (hasLeave) ids.add(item.employee_id)
  })
  return ids
}
