import { describe, expect, it } from 'vitest'

import { goodWhenLabel, unitKind } from './usage-metric-catalog-helpers'

describe('usage metric catalog helpers', () => {
  it('maps backend units to display kinds, unknown falls back to count', () => {
    expect(unitKind('min')).toBe('minutes')
    expect(unitKind('minute_of_day')).toBe('clock')
    expect(unitKind('flag')).toBe('count')
    expect(unitKind('zzz')).toBe('count')
  })

  it('names the good direction', () => {
    expect(goodWhenLabel(1)).toBe('Cao')
    expect(goodWhenLabel(-1)).toBe('Thấp')
    expect(goodWhenLabel(0)).toBe('Không phán xét')
  })
})
