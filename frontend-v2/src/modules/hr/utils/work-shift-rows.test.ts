import { describe, expect, it } from 'vitest'

import {
  shiftTotalStats,
  endHourOptions,
  nextFreeHourBlock,
  rangesToRows,
  rowsToSegments,
  START_HOUR_OPTIONS,
  totalRowHours,
  validateShiftRows,
  withStartHour,
  type ShiftRow,
} from './work-shift-rows'

const row = (id: string, start: number, end: number): ShiftRow => ({ id, start, end })

describe('rows ↔ API segments', () => {
  it('round-trips and sorts by start only at save time (rows keep the typed order)', () => {
    const rows = [row('a', 20, 23), row('b', 8, 10), row('c', 14, 16)]
    expect(rows.map((r) => r.start)).toEqual([20, 8, 14])
    expect(rowsToSegments(rows)).toEqual([
      { start_hour: 8, end_hour: 10 },
      { start_hour: 14, end_hour: 16 },
      { start_hour: 20, end_hour: 23 },
    ])
    expect(rangesToRows([[8, 10]], 'p')).toEqual([{ id: 'p0', start: 8, end: 10 }])
  })

  it('no row = day off: empty segments, total says no workday', () => {
    expect(rowsToSegments([])).toEqual([])
    expect(shiftTotalStats([])).toEqual({ hours: '0 giờ', workday: 'Không tính' })
  })

  it('total counts hours and a shift day is ONE workday whatever the hours (Q3)', () => {
    const rows = [row('a', 8, 10), row('b', 14, 16), row('c', 20, 23)]
    expect(totalRowHours(rows)).toBe(7)
    expect(shiftTotalStats(rows)).toEqual({ hours: '7 giờ', workday: '1 ngày' })
    expect(shiftTotalStats([row('a', 19, 20)])).toEqual({ hours: '1 giờ', workday: '1 ngày' })
    //  Đang sửa dở (hai khung trùng): tổng không đếm phần trùng hai lần.
    expect(totalRowHours([row('a', 8, 12), row('b', 10, 14)])).toBe(6)
  })
})

describe('validateShiftRows', () => {
  it('accepts touching ranges (08–10 and 10–12 do not overlap)', () => {
    expect(validateShiftRows([row('a', 8, 10), row('b', 10, 12)]).valid).toBe(true)
  })

  it('flags Đến ≤ Từ on that row only', () => {
    const v = validateShiftRows([row('a', 10, 10), row('b', 14, 12), row('c', 18, 20)])
    expect(v.rowErrors).toEqual({ a: 'Giờ kết thúc phải sau giờ bắt đầu.', b: 'Giờ kết thúc phải sau giờ bắt đầu.' })
    expect(v.valid).toBe(false)
  })

  it('flags an overlap on BOTH rows, naming the other row by its displayed number', () => {
    const v = validateShiftRows([row('a', 8, 12), row('b', 13, 17), row('c', 11, 14)])
    expect(v.rowErrors).toEqual({
      a: 'Trùng giờ với khung 3.',
      b: 'Trùng giờ với khung 3.',
      c: 'Trùng giờ với khung 1.',
    })
  })

  it('a row identical to another is an overlap too', () => {
    expect(validateShiftRows([row('a', 8, 9), row('b', 8, 9)]).rowErrors).toEqual({
      a: 'Trùng giờ với khung 2.',
      b: 'Trùng giờ với khung 1.',
    })
  })

  it('out of 00:00–24:00 or fractional hours are refused (tampered state)', () => {
    const v = validateShiftRows([row('a', -1, 3), row('b', 22, 25), row('c', 1.5, 3)])
    expect(Object.keys(v.rowErrors)).toEqual(['a', 'b', 'c'])
  })

  it('more than 12 rows is a list error (backend cap)', () => {
    const twelve = Array.from({ length: 12 }, (_, i) => row(`r${i}`, i * 2, i * 2 + 1))
    expect(validateShiftRows(twelve).valid).toBe(true)
    const thirteen = [...twelve, row('x', 23, 24)]
    expect(validateShiftRows(thirteen).formError).toBe('Mỗi ngày tối đa 12 khung giờ — hãy gộp hoặc xóa bớt.')
  })

  it('an empty list is valid (= day off)', () => {
    expect(validateShiftRows([]).valid).toBe(true)
  })
})

describe('nextFreeHourBlock', () => {
  it('a new row is the hour right after the LATEST end', () => {
    expect(nextFreeHourBlock([row('a', 8, 10), row('b', 14, 16)])).toEqual({ start: 16, end: 17 })
  })

  it('starts at 08:00 on an empty day', () => {
    expect(nextFreeHourBlock([])).toEqual({ start: 8, end: 9 })
  })

  it('a day already ending at 24:00 wraps to the first free hour', () => {
    expect(nextFreeHourBlock([row('a', 0, 2), row('b', 20, 24)])).toEqual({ start: 2, end: 3 })
  })

  it('no free hour or already 12 rows → null (button disabled)', () => {
    expect(nextFreeHourBlock([row('a', 0, 24)])).toBeNull()
    expect(nextFreeHourBlock(Array.from({ length: 12 }, (_, i) => row(`r${i}`, i, i + 1)))).toBeNull()
  })
})

describe('hour options', () => {
  it('Từ offers 00:00–23:00; Đến offers only hours after Từ, up to 24:00', () => {
    expect(START_HOUR_OPTIONS).toHaveLength(24)
    expect(START_HOUR_OPTIONS.at(-1)).toBe(23)
    expect(endHourOptions(8)[0]).toBe(9)
    expect(endHourOptions(8).at(-1)).toBe(24)
    expect(endHourOptions(23)).toEqual([24])
    //  Giá trị hỏng không làm danh sách rỗng hay âm.
    expect(endHourOptions(-5)[0]).toBe(1)
    expect(endHourOptions(30)).toEqual([24])
  })

  it('moving Từ past Đến pushes Đến along, keeping the length, clamped at 24:00', () => {
    expect(withStartHour(row('a', 8, 10), 14)).toEqual(row('a', 14, 16))
    expect(withStartHour(row('a', 8, 12), 22)).toEqual(row('a', 22, 24))
    //  Đến vẫn sau Từ mới thì giữ nguyên.
    expect(withStartHour(row('a', 8, 17), 9)).toEqual(row('a', 9, 17))
  })
})
