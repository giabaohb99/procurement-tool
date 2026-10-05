import { describe, expect, it } from 'vitest'

import type { WorkRosterCell, WorkRosterItem, WorkRosterLeave } from '../types/work-roster'
import { indexCellsByDate } from './work-roster-cell'
import { groupByDepartment, pickLeaveRowIds, summarizeRosterDay } from './work-roster-summary'

const leave = (over: Partial<WorkRosterLeave> = {}): WorkRosterLeave => ({
  request_id: 12,
  code: 'NP012',
  leave_type_name: 'Phép năm',
  status: 3,
  status_label: 'Đã duyệt',
  is_approved: true,
  morning: true,
  afternoon: true,
  ...over,
})

const cell = (over: Partial<WorkRosterCell> = {}): WorkRosterCell => ({
  date: '2026-10-05',
  work_kind: 2,
  start_time: '08:00',
  end_time: '17:00',
  schedule_name: 'Hành chính',
  is_holiday: false,
  holiday_name: '',
  leave: null,
  ...over,
})

const item = (id: number, dept: number, deptName: string, cells: WorkRosterCell[]): WorkRosterItem => ({
  employee_id: id,
  code: `NV${id}`,
  full_name: `Người ${id}`,
  department_id: dept,
  department_name: deptName,
  cells,
})

describe('summarizeRosterDay', () => {
  const day = '2026-10-05'
  const items = [
    item(1, 4, 'IT', [cell()]),
    item(2, 4, 'IT', [cell({ leave: leave() })]),
    item(3, 4, 'IT', [cell({ leave: leave({ afternoon: false }) })]),
    item(4, 4, 'IT', [cell({ work_kind: 1 })]),
    item(5, 4, 'IT', [cell({ is_holiday: true })]),
    item(6, 4, 'IT', []),
  ]

  it('counts a half-day leave as working, leave/scheduled-off/holiday as off, and skips missing cells', () => {
    expect(summarizeRosterDay(items.map(indexCellsByDate), day)).toEqual({ working: 2, off: 3 })
  })

  it('returns 0 / 0 for an empty list and for a date absent from the data', () => {
    expect(summarizeRosterDay([], day)).toEqual({ working: 0, off: 0 })
    expect(summarizeRosterDay(items.map(indexCellsByDate), '2030-01-01')).toEqual({ working: 0, off: 0 })
  })
})

describe('groupByDepartment', () => {
  it('keeps backend order and groups by department_id', () => {
    const groups = groupByDepartment([
      item(1, 4, 'IT', []),
      item(2, 4, 'IT', []),
      item(3, 7, 'Kế toán', []),
    ])
    expect(groups.map((g) => [g.departmentName, g.items.length])).toEqual([
      ['IT', 2],
      ['Kế toán', 1],
    ])
  })

  it('treats department_id 0 as a real group and labels a blank name', () => {
    const groups = groupByDepartment([item(1, 0, '  ', [])])
    expect(groups).toHaveLength(1)
    expect(groups[0].departmentName).toBe('Chưa có phòng ban')
  })

  it('returns an empty array for an empty list', () => {
    expect(groupByDepartment([])).toEqual([])
  })
})


describe('pickLeaveRowIds', () => {
  const days = [{ date: '2026-10-05' }, { date: '2026-10-06' }, { date: '2026-10-07' }]
  const day = (date: string, over: Partial<WorkRosterCell> = {}) => cell({ date, ...over })
  const pick = (items: WorkRosterItem[]) => [...pickLeaveRowIds(items, items.map(indexCellsByDate), days)]

  it('returns nothing for an empty roster or when nobody has leave', () => {
    expect(pick([])).toEqual([])
    expect(pick([item(1, 4, 'IT', days.map((d) => day(d.date)))])).toEqual([])
  })

  //  05/10/2026: hàng dính CHỒNG theo thứ tự trên lưới — sắp lại theo ngày nghỉ (bản khối ghim cũ)
  //  thì hàng dưới nhảy lên trên hàng trên khi cuộn.
  it('keeps grid order instead of re-sorting by first leave date, and survives missing cells', () => {
    const late = item(1, 4, 'IT', [day('2026-10-07', { leave: leave() })])
    const early = item(2, 4, 'IT', [day('2026-10-05', { leave: leave() })])
    const none = item(3, 4, 'IT', [])
    expect(pick([late, early, none])).toEqual([1, 2])
  })

  it('counts pending and half-day leave but not leave on a scheduled-off or holiday cell', () => {
    const pending = item(1, 4, 'IT', [day('2026-10-05', { leave: leave({ is_approved: false }) })])
    const half = item(2, 4, 'IT', [day('2026-10-05', { leave: leave({ afternoon: false }) })])
    const off = item(3, 4, 'IT', [day('2026-10-05', { work_kind: 1, leave: leave() })])
    const holiday = item(4, 4, 'IT', [day('2026-10-05', { is_holiday: true, leave: leave() })])
    expect(pick([pending, half, off, holiday])).toEqual([1, 2])
  })

  //  05/10/2026: bản giới hạn 6 người làm người thứ 7 trở đi trôi bên dưới chỗ dính — nay ai có nghỉ cũng dính.
  it('returns every person with leave, with no cap', () => {
    const many = Array.from({ length: 30 }, (_, i) => item(i + 1, 4, 'IT', [day('2026-10-05', { leave: leave() })]))
    expect(pick(many)).toHaveLength(30)
  })
})
