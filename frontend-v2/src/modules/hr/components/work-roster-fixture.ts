import type { WorkRoster, WorkRosterCell, WorkRosterItem, WorkRosterLeave } from '../types/work-roster'

/** Dữ liệu mẫu cho bài kiểm «Xem lịch». Ngày truyền cụ thể — không phụ thuộc «hôm nay». */
export const ROSTER_DAYS = [
  { date: '2026-10-05', weekday: 0, holiday_name: '' },
  { date: '2026-10-06', weekday: 1, holiday_name: 'Nghỉ bù' },
  { date: '2026-10-11', weekday: 6, holiday_name: '' },
]

export function rosterLeave(over: Partial<WorkRosterLeave> = {}): WorkRosterLeave {
  return {
    request_id: 12,
    code: 'NP012',
    leave_type_name: 'Phép năm',
    status: 3,
    status_label: 'Đã duyệt',
    is_approved: true,
    morning: true,
    afternoon: true,
    ...over,
  }
}

export function rosterCell(date: string, over: Partial<WorkRosterCell> = {}): WorkRosterCell {
  return {
    date,
    work_kind: 2,
    start_time: '08:00',
    end_time: '17:00',
    schedule_name: 'Hành chính',
    is_holiday: false,
    holiday_name: '',
    leave: null,
    ...over,
  }
}

export function rosterItem(
  id: number,
  name: string,
  dept: { id: number; name: string },
  cells: WorkRosterCell[],
): WorkRosterItem {
  return {
    employee_id: id,
    code: `NV${id}`,
    full_name: name,
    department_id: dept.id,
    department_name: dept.name,
    cells,
  }
}

export function rosterResponse(items: WorkRosterItem[], total = items.length): WorkRoster {
  return { from_date: '2026-10-05', to_date: '2026-10-11', days: ROSTER_DAYS, total, items }
}
