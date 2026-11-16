import { describe, expect, it } from 'vitest'

import type { WorkRosterCell, WorkRosterItem, WorkRosterLeave } from '../types/work-roster'
import { describeRosterCell, formatHour, indexCellsByDate, shiftCellLines } from './work-roster-cell'

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

describe('formatHour', () => {
  //  05/10/2026: "08–17" bị chê — giờ luôn hiện đủ HH:MM.
  it('always renders full HH:MM and never breaks on bad input', () => {
    expect(formatHour('08:00')).toBe('08:00')
    expect(formatHour('8:30')).toBe('08:30')
    expect(formatHour('17:00:00')).toBe('17:00')
    expect(formatHour('')).toBe('')
    expect(formatHour(null)).toBe('')
    expect(formatHour(undefined)).toBe('')
    expect(formatHour('abc')).toBe('')
  })
})

describe('describeRosterCell', () => {
  it('treats a missing cell or unknown work_kind as unknown and never counts it as working', () => {
    expect(describeRosterCell(undefined).state).toBe('unknown')
    expect(describeRosterCell(cell({ work_kind: 0 })).state).toBe('unknown')
    expect(describeRosterCell(cell({ work_kind: 99 })).isWorking).toBe(false)
  })

  //  Lễ RIÊNG của pháp nhân người đó nằm ở ô, không ở tiêu đề cột (chỉ mang lễ chung).
  it('holiday with an empty name still reads as a holiday instead of printing "undefined"', () => {
    const v = describeRosterCell(cell({ is_holiday: true, holiday_name: '' }))
    expect(v).toMatchObject({ state: 'holiday', description: 'Ngày lễ' })
  })

  it('shows the full HH:MM range for a full working day', () => {
    const v = describeRosterCell(cell())
    expect(v).toMatchObject({ state: 'working', shortLabel: '08:00 – 17:00', isWorking: true })
  })

  it('falls back to the word Làm when hours are missing instead of an empty cell', () => {
    expect(describeRosterCell(cell({ start_time: null, end_time: null })).shortLabel).toBe('Làm')
  })

  it('labels half-day schedules as Sáng or Chiều', () => {
    expect(describeRosterCell(cell({ work_kind: 3 })).shortLabel).toBe('Sáng')
    expect(describeRosterCell(cell({ work_kind: 4 })).shortLabel).toBe('Chiều')
  })

  it('marks a scheduled day off as off and not working', () => {
    const v = describeRosterCell(cell({ work_kind: 1, start_time: null, end_time: null }))
    expect(v).toMatchObject({ state: 'off', shortLabel: 'Nghỉ', isWorking: false })
  })

  it('lets a holiday beat both the schedule and a leave request, and names it in the description', () => {
    const v = describeRosterCell(cell({ is_holiday: true, holiday_name: 'Quốc khánh', leave: leave() }))
    expect(v.state).toBe('holiday')
    expect(v.leaveRequestId).toBeNull()
    expect(v.description).toContain('Quốc khánh')
  })

  it('shows a full-day leave with its type name and a link target to the request', () => {
    const v = describeRosterCell(cell({ leave: leave() }))
    expect(v).toMatchObject({
      state: 'leave',
      shortLabel: 'Phép năm',
      leaveRequestId: 12,
      isPending: false,
      isWorking: false,
    })
  })

  it('flags a pending request as isPending (dashed border)', () => {
    const v = describeRosterCell(cell({ leave: leave({ is_approved: false, status: 2 }) }))
    expect(v.isPending).toBe(true)
    expect(v.description).toContain('chờ duyệt')
  })

  it('keeps working in the afternoon when only the morning is off', () => {
    const v = describeRosterCell(cell({ leave: leave({ morning: true, afternoon: false }) }))
    expect(v).toMatchObject({
      state: 'partial',
      shortLabel: 'Nghỉ sáng',
      morningOff: true,
      afternoonOff: false,
      isWorking: true,
    })
  })

  it('keeps working in the morning when only the afternoon is off, with a label distinct from a morning-only schedule', () => {
    const v = describeRosterCell(cell({ leave: leave({ morning: false, afternoon: true }) }))
    //  Lỗi 05/10/2026: ô ghi "Sáng" trùng chữ với ngày lịch chỉ làm buổi sáng → đọc ngược nghĩa.
    expect(v).toMatchObject({ state: 'partial', shortLabel: 'Nghỉ chiều', afternoonOff: true })
    expect(v.shortLabel).not.toBe(describeRosterCell(cell({ work_kind: 3 })).shortLabel)
  })

  it('treats leave over the only scheduled half as a whole day off, not a partial', () => {
    const v = describeRosterCell(cell({ work_kind: 3, leave: leave({ morning: true, afternoon: false }) }))
    expect(v.state).toBe('leave')
  })

  it('ignores leave that only covers a half the person does not work', () => {
    const v = describeRosterCell(cell({ work_kind: 3, leave: leave({ morning: false, afternoon: true }) }))
    expect(v).toMatchObject({ state: 'working', leaveRequestId: null })
  })

  it('leaves a scheduled day off unchanged when a request overlaps it', () => {
    expect(describeRosterCell(cell({ work_kind: 1, leave: leave() })).state).toBe('off')
  })

  it('ignores a malformed request with both halves false', () => {
    const v = describeRosterCell(cell({ leave: leave({ morning: false, afternoon: false }) }))
    expect(v.state).toBe('working')
  })

  it('treats request_id 0 as a real request, not as no request', () => {
    expect(describeRosterCell(cell({ leave: leave({ request_id: 0 }) })).leaveRequestId).toBe(0)
  })
})

describe('indexCellsByDate', () => {
  it('keeps the last cell when a date is duplicated without breaking', () => {
    const item: WorkRosterItem = {
      employee_id: 1,
      code: 'NV1',
      full_name: 'Người 1',
      department_id: 1,
      department_name: 'A',
      cells: [cell({ schedule_name: 'a' }), cell({ schedule_name: 'b' })],
    }
    const map = indexCellsByDate(item)
    expect(map.size).toBe(1)
    expect(map.get('2026-10-05')?.schedule_name).toBe('b')
  })
})

describe('describeRosterCell — shifts by day (duoc-CR-761)', () => {
  const shift = (segments: string[], ranges: number[][], hours: number, note = '') => ({
    is_shift: true,
    shift: { segments, ranges, hours, note, is_day_off: segments.length === 0 },
    schedule_name: 'Xếp ca theo ngày',
  })

  it('a shift day is an exception: full HH:MM segments, hours glyph for the month view', () => {
    const view = describeRosterCell(cell({ ...shift(['08:00–10:00', '14:00–16:00'], [[8, 10], [14, 16]], 4), end_time: '16:00' }))
    expect(view).toMatchObject({
      state: 'working',
      isShift: true,
      isWorking: true,
      shortLabel: '08:00–10:00 · 14:00–16:00',
      glyph: '4h',
      shiftLines: ['08:00–10:00', '14:00–16:00'],
    })
    expect(view.description).toBe('Ca xếp theo ngày: 08:00–10:00 · 14:00–16:00 (4 giờ)')
  })

  it('a day off set by shift is still "off" for the counters but flagged as a shift exception', () => {
    const view = describeRosterCell(cell({ work_kind: 1, start_time: null, end_time: null, ...shift([], [], 0, 'Đổi ca') }))
    expect(view).toMatchObject({ state: 'off', isShift: true, isWorking: false, shortLabel: 'Nghỉ (xếp ca)', glyph: 'N' })
    expect(view.description).toBe('Nghỉ cả ngày do xếp ca — Đổi ca')
  })

  it('leave keeps priority on a shift day and the tooltip still names the shift', () => {
    const view = describeRosterCell(
      cell({ work_kind: 2, ...shift(['08:00–10:00', '14:00–16:00'], [[8, 10], [14, 16]], 4), leave: leave({ morning: true, afternoon: false }) }),
    )
    expect(view.state).toBe('partial')
    expect(view.isShift).toBe(true)
    expect(view.description).toContain('Ca xếp theo ngày: 08:00–10:00 · 14:00–16:00')
  })

  it('a holiday stays a holiday even with a shift, and the shift is mentioned', () => {
    const view = describeRosterCell(cell({ is_holiday: true, holiday_name: 'Quốc khánh', ...shift(['08:00–12:00'], [[8, 12]], 4) }))
    expect(view.state).toBe('holiday')
    expect(view.description).toBe('Ngày lễ: Quốc khánh · Ca xếp theo ngày: 08:00–12:00 (4 giờ)')
  })

  it('is_shift without a shift block (or an old backend) behaves exactly like before', () => {
    expect(describeRosterCell(cell({ is_shift: true, shift: null }))).toMatchObject({ isShift: false, shortLabel: '08:00 – 17:00' })
    expect(describeRosterCell(cell())).toMatchObject({ isShift: false, shiftLines: [] })
  })
})

describe('shiftCellLines', () => {
  it('one or two segments: one per line; three or more: first + count and hours', () => {
    expect(shiftCellLines([], 0)).toEqual([])
    expect(shiftCellLines(['08:00–10:00'], 2)).toEqual(['08:00–10:00'])
    expect(shiftCellLines(['06:00–07:00', '12:00–13:00', '20:00–24:00'], 6)).toEqual(['06:00–07:00 …', '3 khung · 6 giờ'])
  })
})
