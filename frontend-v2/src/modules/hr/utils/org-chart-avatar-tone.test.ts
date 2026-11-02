import { describe, expect, it } from 'vitest'

import { pickOrgChartAvatarTone } from './org-chart-avatar-tone'

describe('pickOrgChartAvatarTone', () => {
  it('is stable for the same person and spreads neighbours over different tones', () => {
    expect(pickOrgChartAvatarTone(7)).toBe(pickOrgChartAvatarTone(7))
    expect(new Set([1, 2, 3, 4, 5].map(pickOrgChartAvatarTone)).size).toBe(5)
  })

  it('never returns undefined for negative, fractional, NaN or infinite ids', () => {
    for (const id of [-3, 2.7, Number.NaN, Number.POSITIVE_INFINITY, 0]) {
      expect(pickOrgChartAvatarTone(id)).toMatch(/^bg-/)
    }
  })
})
