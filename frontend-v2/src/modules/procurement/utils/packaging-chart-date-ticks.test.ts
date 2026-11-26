import { describe, expect, it } from 'vitest'

import { dateTickAnchor, pickDateTickIndexes } from './packaging-chart-date-ticks'

const labels = (n: number) => Array.from({ length: n }, () => '22/10/26')
const linear = (n: number, from = 52, to = 986) => Array.from({ length: n }, (_, i) => from + (i * (to - from)) / (n - 1))

describe('pickDateTickIndexes', () => {
  it('keeps first and last and drops a step label that would touch the last one', () => {
    //  52 điểm, step 6: điểm 48 (x ~ 908) nằm sát điểm cuối 51 (x ~ 986) → nhãn 48 phải bị bỏ.
    const xs = linear(52)
    const picked = pickDateTickIndexes(xs, labels(52), 6)
    expect(picked[0]).toBe(0)
    expect(picked.at(-1)).toBe(51)
    expect(picked).not.toContain(48)
  })

  it('never lets two kept labels overlap', () => {
    for (const count of [2, 3, 5, 11, 12, 27, 52, 101]) {
      const xs = linear(count)
      const step = Math.max(1, Math.ceil(count / 10))
      const picked = pickDateTickIndexes(xs, labels(count), step)
      for (let k = 1; k < picked.length; k += 1) {
        const gap = xs[picked[k]] - xs[picked[k - 1]]
        expect(gap).toBeGreaterThanOrEqual(48)
      }
    }
  })

  it('handles empty and single-point series', () => {
    expect(pickDateTickIndexes([], [], 1)).toEqual([])
    expect(pickDateTickIndexes([500], ['01/01/26'], 1)).toEqual([0])
  })
})

describe('dateTickAnchor', () => {
  it('anchors the ends outward and centres the rest', () => {
    expect(dateTickAnchor(0, 5)).toBe('start')
    expect(dateTickAnchor(4, 5)).toBe('end')
    expect(dateTickAnchor(2, 5)).toBe('middle')
    expect(dateTickAnchor(0, 1)).toBe('start')
  })
})
