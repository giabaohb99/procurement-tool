import { describe, expect, it } from 'vitest'

import { kpiGridColumnsClass } from './kpi-grid-columns'

describe('kpiGridColumnsClass', () => {
  it('never leaves a lone card on its own row for 3, 5 or 6 cards', () => {
    expect(kpiGridColumnsClass(5)).toBe('xl:grid-cols-5')
    expect(kpiGridColumnsClass(6)).toBe('xl:grid-cols-3')
    expect(kpiGridColumnsClass(3)).toBe('xl:grid-cols-3')
  })

  it('falls back to 4 columns for 4 cards and for larger or empty sets', () => {
    expect(kpiGridColumnsClass(4)).toBe('xl:grid-cols-4')
    expect(kpiGridColumnsClass(8)).toBe('xl:grid-cols-4')
    expect(kpiGridColumnsClass(0)).toBe('xl:grid-cols-4')
  })
})
