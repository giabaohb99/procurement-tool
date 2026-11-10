import { describe, expect, it } from 'vitest'

import {
  byIdDescending,
  compareSortValues,
  isBlankSortValue,
  sortRowsBy,
  type SortValue,
} from './compare-sort-values'

const BLANKS: SortValue[] = [null, undefined, '', ' ', '   ', '\t\n']

function sortValues(values: SortValue[], dir: 'asc' | 'desc' = 'asc'): SortValue[] {
  return sortRowsBy(values, (v) => v, dir)
}

describe('isBlankSortValue', () => {
  it('flags null, undefined, empty and whitespace-only strings only', () => {
    for (const blank of BLANKS) expect(isBlankSortValue(blank)).toBe(true)
    // 0, false và "0" là giá trị thật: lẫn vào ô trống là dòng "0 ngày" biến mất xuống đáy.
    for (const filled of [0, -0, false, '0', 'a', ' a ']) expect(isBlankSortValue(filled)).toBe(false)
  })
})

describe('compareSortValues', () => {
  it('puts blank cells LAST in both directions, whitespace included', () => {
    for (const blank of BLANKS) {
      for (const dir of ['asc', 'desc'] as const) {
        expect(compareSortValues(blank, 'a', dir)).toBeGreaterThan(0)
        expect(compareSortValues('a', blank, dir)).toBeLessThan(0)
        expect(compareSortValues(blank, 0, dir)).toBeGreaterThan(0)
      }
    }
  })

  it('treats two blanks as equal, whatever kind of blank', () => {
    for (const a of BLANKS) for (const b of BLANKS) expect(compareSortValues(a, b, 'desc')).toBe(0)
  })

  it('keeps 0 and false as real values, not blanks', () => {
    expect(compareSortValues(0, 5, 'asc')).toBeLessThan(0)
    expect(compareSortValues(0, null, 'asc')).toBeLessThan(0)
    expect(compareSortValues(0, null, 'desc')).toBeLessThan(0)
    expect(compareSortValues(false, undefined, 'desc')).toBeLessThan(0)
  })

  it('compares numeric strings as numbers: 12.5 is bigger than 12.25', () => {
    expect(compareSortValues('12.5', '12.25')).toBeGreaterThan(0)
    expect(compareSortValues('12.25', '12.5', 'desc')).toBeGreaterThan(0)
    // Chuỗi Decimal của API: số 0 thừa đuôi không đổi giá trị.
    expect(compareSortValues('1000.000', '1000')).toBe(0)
  })

  it('handles negative numbers, in numbers and in numeric text', () => {
    expect(compareSortValues('-3', '2')).toBeLessThan(0)
    expect(compareSortValues(-3, -10)).toBeGreaterThan(0)
    expect(sortValues(['2', '-3', '-10', '0']).join(',')).toBe('-10,-3,0,2')
  })

  it('mixes number and numeric text on the numeric rule', () => {
    expect(compareSortValues(9, '10')).toBeLessThan(0)
    expect(compareSortValues('9', 10)).toBeLessThan(0)
  })

  it('sorts Vietnamese accents next to the base letter: an < ảnh < bao', () => {
    expect(sortValues(['bao', 'ảnh', 'an'])).toEqual(['an', 'ảnh', 'bao'])
  })

  it('puts Đ right after D, before E', () => {
    expect(sortValues(['E', 'Đ', 'D', 'C'])).toEqual(['C', 'D', 'Đ', 'E'])
  })

  it('is case-insensitive', () => {
    expect(compareSortValues('An', 'an')).toBe(0)
    expect(compareSortValues('ÂN', 'ân')).toBe(0)
  })

  it('reads digits inside text by value: "Option 2" < "Option 10"', () => {
    expect(compareSortValues('Option 2', 'Option 10')).toBeLessThan(0)
    expect(sortValues(['PO10', 'PO9', 'PO100'])).toEqual(['PO9', 'PO10', 'PO100'])
  })

  it('sorts ISO dates as text in the right order', () => {
    expect(sortValues(['2026-11-10', '2026-02-01', '2025-12-31'])).toEqual([
      '2025-12-31',
      '2026-02-01',
      '2026-11-10',
    ])
  })

  it('orders booleans as 0 / 1', () => {
    expect(compareSortValues(false, true)).toBeLessThan(0)
    expect(compareSortValues(true, false, 'desc')).toBeLessThan(0)
    expect(compareSortValues(true, true)).toBe(0)
  })

  it('never yields NaN for a boolean mixed with text or numbers', () => {
    expect(Number.isNaN(compareSortValues(true, 'abc'))).toBe(false)
    expect(Number.isNaN(compareSortValues('abc', false, 'desc'))).toBe(false)
    expect(compareSortValues(true, 1)).toBe(0)
  })

  it('falls back to text when only one side is numeric', () => {
    // Số đứng trước chữ theo collator; điều cần giữ là KHÔNG ném lỗi và có thứ tự ổn định.
    expect(compareSortValues('12', 'abc')).toBeLessThan(0)
    expect(compareSortValues('abc', 12)).toBeGreaterThan(0)
    expect(compareSortValues('1e3', '5')).not.toBeNaN()
  })

  it('does not treat lookalikes of numbers as numbers', () => {
    // "1,5" / "1e3" / ".5" không khớp mẫu số thuần: đi đường chữ, không thành NaN.
    for (const odd of ['1,5', '1e3', '.5', '5.', '0x10', 'Infinity', 'NaN']) {
      expect(Number.isNaN(compareSortValues(odd, '2'))).toBe(false)
    }
  })

  it('returns a consistent antisymmetric order', () => {
    const samples: SortValue[] = ['b', 'A', 'ă', '', 3, '3.5', false, true, null, 'Đ']
    for (const a of samples) {
      for (const b of samples) {
        for (const dir of ['asc', 'desc'] as const) {
          expect(Math.sign(compareSortValues(a, b, dir))).toBe(0 - Math.sign(compareSortValues(b, a, dir)))
        }
      }
    }
  })
})

describe('sortRowsBy', () => {
  interface Row {
    id: number
    v: SortValue
  }
  const rows: Row[] = [
    { id: 1, v: 'b' },
    { id: 2, v: null },
    { id: 3, v: 'a' },
    { id: 4, v: '  ' },
    { id: 5, v: 'a' },
  ]
  const ids = (list: Row[]) => list.map((r) => r.id)
  const byV = (r: Row) => r.v

  it('keeps blanks last in both directions and does not flip them on desc', () => {
    expect(ids(sortRowsBy(rows, byV, 'asc'))).toEqual([3, 5, 1, 2, 4])
    expect(ids(sortRowsBy(rows, byV, 'desc'))).toEqual([1, 3, 5, 2, 4])
  })

  it('keeps the original order of equal rows when no tie-break is given', () => {
    expect(ids(sortRowsBy(rows, byV, 'asc')).slice(0, 2)).toEqual([3, 5])
    expect(ids(sortRowsBy(rows, byV, 'desc')).slice(0, 2)).toEqual([1, 3])
  })

  it('applies the tie-break to equal rows (and to blanks) without flipping it on desc', () => {
    expect(ids(sortRowsBy(rows, byV, 'asc', byIdDescending))).toEqual([5, 3, 1, 4, 2])
    expect(ids(sortRowsBy(rows, byV, 'desc', byIdDescending))).toEqual([1, 5, 3, 4, 2])
  })

  it('reads each row value once and never mutates the input', () => {
    const input = [...rows]
    let calls = 0
    sortRowsBy(input, (r) => (calls++, r.v), 'asc')
    expect(calls).toBe(rows.length)
    expect(ids(input)).toEqual(ids(rows))
  })

  it('copes with empty, single and all-equal lists', () => {
    expect(sortRowsBy([], byV, 'asc')).toEqual([])
    expect(sortRowsBy([rows[0]], byV, 'desc')).toEqual([rows[0]])
    const same = [{ id: 1, v: 'x' }, { id: 2, v: 'x' }, { id: 3, v: 'X' }]
    expect(ids(sortRowsBy(same, byV, 'desc'))).toEqual([1, 2, 3])
  })

  it('survives a long list with many blanks', () => {
    const big: Row[] = Array.from({ length: 5000 }, (_, i) => ({ id: i, v: i % 3 === 0 ? null : i % 97 }))
    const out = sortRowsBy(big, byV, 'desc', byIdDescending)
    const firstBlank = out.findIndex((r) => isBlankSortValue(r.v))
    expect(out.slice(firstBlank).every((r) => isBlankSortValue(r.v))).toBe(true)
    expect(out[0].v).toBe(96)
  })
})

describe('byIdDescending', () => {
  it('puts the larger id first', () => {
    expect(byIdDescending({ id: 1 }, { id: 2 })).toBeGreaterThan(0)
    expect(byIdDescending({ id: 3 }, { id: 3 })).toBe(0)
  })
})
