import { describe, expect, it } from 'vitest'

import { formatReportRange } from './format-report-range'

describe('formatReportRange', () => {
  it('prints a single date for one-day periods instead of "d – d"', () => {
    expect(formatReportRange('2026-09-28', '2026-09-28')).toBe('28/09/2026')
  })

  it('prints both ends for longer periods', () => {
    expect(formatReportRange('2026-09-01', '2026-09-28')).toBe('01/09/2026 – 28/09/2026')
  })

  it('returns empty when the period is not known yet, and one date when the end is missing', () => {
    expect(formatReportRange('', '')).toBe('')
    expect(formatReportRange('2026-09-01', '')).toBe('01/09/2026')
  })
})
