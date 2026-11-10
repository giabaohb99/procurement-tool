import { describe, expect, it } from 'vitest'

import { sortRowsByCell, type CellGetters } from './sort-rows-by-cell'

interface Row {
  id: number
  name: string | null
  days: number | null
}

const getters: CellGetters<Row> = {
  name: (r) => r.name,
  days: (r) => r.days,
}

const rows: Row[] = [
  { id: 1, name: 'Bình', days: 1 },
  { id: 2, name: '', days: 0.5 },
  { id: 3, name: 'An', days: null },
  { id: 4, name: null, days: 1 },
  { id: 5, name: 'an', days: 1 },
]

const ids = (list: Row[]) => list.map((r) => r.id)

describe('sortRowsByCell', () => {
  it('puts blank cells last in BOTH directions, never flipped by desc', () => {
    // Bug lớp này: xếp giảm dần lật cả rổ ô trống lên đầu -> bấm cột nhìn như không ăn.
    const asc = sortRowsByCell(rows, 'name', 'asc', getters)
    const desc = sortRowsByCell(rows, 'name', 'desc', getters)
    expect(ids(asc).slice(-2).sort()).toEqual([2, 4])
    expect(ids(desc).slice(-2).sort()).toEqual([2, 4])
  })

  it('compares text case-insensitively with id desc as the tie-break for equal cells', () => {
    // "An" và "an" bằng nhau theo sensitivity base -> hạ xuống khóa phụ id giảm dần (5 trước 3).
    expect(ids(sortRowsByCell(rows, 'name', 'asc', getters))).toEqual([5, 3, 1, 4, 2])
  })

  it('follows the Vietnamese alphabet: A < Ă < Â < B, and compares numbers inside text by value', () => {
    const vi: Row[] = [
      { id: 1, name: 'Bình', days: null },
      { id: 2, name: 'Âu', days: null },
      { id: 3, name: 'An', days: null },
      { id: 4, name: 'Ăn', days: null },
      { id: 5, name: 'PO10', days: null },
      { id: 6, name: 'PO9', days: null },
    ]
    expect(ids(sortRowsByCell(vi, 'name', 'asc', getters))).toEqual([3, 4, 2, 1, 6, 5])
  })

  it('treats numeric 0 as a real value, not blank', () => {
    const withZero: Row[] = [
      { id: 1, name: 'a', days: 0 },
      { id: 2, name: 'b', days: null },
      { id: 3, name: 'c', days: 2 },
    ]
    expect(ids(sortRowsByCell(withZero, 'days', 'asc', getters))).toEqual([1, 3, 2])
    expect(ids(sortRowsByCell(withZero, 'days', 'desc', getters))).toEqual([3, 1, 2])
  })

  it('returns an untouched copy for an empty or unknown key and for an empty list', () => {
    const out = sortRowsByCell(rows, '', 'asc', getters)
    expect(out).toEqual(rows)
    expect(out).not.toBe(rows)
    expect(sortRowsByCell(rows, 'nope', 'desc', getters)).toEqual(rows)
    expect(sortRowsByCell([], 'name', 'asc', getters)).toEqual([])
  })

  it('does not mutate the input array', () => {
    const copy = [...rows]
    sortRowsByCell(rows, 'name', 'desc', getters)
    expect(rows).toEqual(copy)
  })

  it('treats undefined and whitespace-only cells as blank and ranks numeric text by value', () => {
    // Hợp từ bài kiểm cũ của sortLoadedRows: ô trống đủ bốn dạng, đứng cuối theo id giảm dần.
    const mixed: Row[] = [
      { id: 1, name: 'Bình', days: 2 },
      { id: 2, name: '', days: 0 },
      { id: 3, name: null, days: 5 },
      { id: 4, name: 'An', days: 2 },
      { id: 5, name: '   ', days: 1 },
    ]
    const asc = ids(sortRowsByCell(mixed, 'name', 'asc', getters))
    const desc = ids(sortRowsByCell(mixed, 'name', 'desc', getters))
    expect(asc).toEqual([4, 1, 5, 3, 2])
    expect(desc).toEqual([1, 4, 5, 3, 2])
    // days = 2 là hai dòng id 4 và 1 -> id lớn trước.
    const byDays = ids(sortRowsByCell(mixed, 'days', 'asc', getters))
    expect(byDays.indexOf(4)).toBeLessThan(byDays.indexOf(1))
    // Chuỗi số so theo số: "12.5" đứng sau "12.25".
    const text: CellGetters<{ id: number; v: string }> = { v: (r) => r.v }
    expect(
      sortRowsByCell([{ id: 1, v: '12.5' }, { id: 2, v: '12.25' }], 'v', 'asc', text).map((r) => r.id),
    ).toEqual([2, 1])
  })
})
