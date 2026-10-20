import { describe, expect, it } from 'vitest'

import { buildHistogramData, buildTrendData, bucketRangeText, medianBucketIndex, weekShortLabel } from './usage-metric-chart-helpers'

describe('usage metric chart helpers', () => {
  it('formats bucket labels by unit', () => {
    expect(bucketRangeText({ lo: 480, hi: 540, count: 1 }, 'minute_of_day')).toBe('08:00 – 08:59')
    expect(bucketRangeText({ lo: 0.1, hi: 0.2, count: 1 }, 'ratio')).toBe('10% – 20%')
    expect(bucketRangeText({ lo: 0, hi: 1, count: 1 }, 'count')).toBe('0')
    expect(bucketRangeText({ lo: 2, hi: 4, count: 1 }, 'count')).toBe('2 – 3')
    expect(bucketRangeText({ lo: 30, hi: null, count: 1 }, 'min')).toBe('≥ 30 phút')
    expect(buildHistogramData([{ lo: 0, hi: 1, count: 4 }, { lo: 1, hi: 2, count: 2 }], 'flag').map((d) => d.label)).toEqual(['Không', 'Có'])
  })

  it('finds the bucket holding the median, 100% falls in the last one', () => {
    const b = [{ lo: 0, hi: 5, count: 1 }, { lo: 5, hi: 10, count: 1 }, { lo: 10, hi: null, count: 1 }]
    expect(medianBucketIndex(b, 5)).toBe(1)
    expect(medianBucketIndex(b, 99)).toBe(2)
    expect(medianBucketIndex(b, null)).toBe(-1)
    expect(medianBucketIndex([{ lo: 0.9, hi: 1, count: 1 }], 1)).toBe(0)
    expect(medianBucketIndex([], 3)).toBe(-1)
  })

  it('shortens week labels and keeps null medians as gaps', () => {
    expect(weekShortLabel('2026-10-12')).toBe('12/10')
    expect(buildTrendData([{ week: '2026-10-05', median: null, measured: 0 }])[0]).toMatchObject({ label: '05/10', value: null })
  })
})
