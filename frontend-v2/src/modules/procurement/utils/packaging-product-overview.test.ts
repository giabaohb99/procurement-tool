import { describe, expect, it } from 'vitest'

import { EMPTY_IMPACT_FILTERS } from './packaging-impact-filters'
import { buildOverviewParams, OVERVIEW_TREND_CHIPS, overviewChipLabel } from './packaging-product-overview'

describe('OVERVIEW_TREND_CHIPS', () => {
  it('takes the four trend labels from the generated code set, in the order the owner reads them', () => {
    expect(OVERVIEW_TREND_CHIPS.map((chip) => [chip.value, chip.label])).toEqual([
      ['all', 'Tất cả'],
      ['up', 'Tăng'],
      ['down', 'Giảm'],
      ['flat', 'Không đổi'],
      ['missing', 'Chưa có giá'],
    ])
  })
})

describe('overviewChipLabel', () => {
  const counts = { all: 1000, up: 263, down: 322, flat: 415, missing: 0 }

  it('appends the vi-VN formatted count, and a zero count is still shown', () => {
    expect(overviewChipLabel(OVERVIEW_TREND_CHIPS[0], counts)).toBe('Tất cả (1.000)')
    expect(overviewChipLabel(OVERVIEW_TREND_CHIPS[1], counts)).toBe('Tăng (263)')
    expect(overviewChipLabel(OVERVIEW_TREND_CHIPS[4], counts)).toBe('Chưa có giá (0)')
  })

  it('shows only the label until the first response arrives', () => {
    expect(overviewChipLabel(OVERVIEW_TREND_CHIPS[2], undefined)).toBe('Giảm')
  })
})

describe('buildOverviewParams', () => {
  it('omits default filters and the sort until the user picks a column', () => {
    expect(buildOverviewParams('all', '  ', { by: '', dir: 'asc' })).toEqual({
      q: undefined,
      trend: undefined,
    })
  })

  it('sends trimmed keyword, trend and sort when set', () => {
    expect(buildOverviewParams('up', ' HH04 ', { by: 'diff_carton', dir: 'desc' })).toEqual({
      q: 'HH04',
      trend: 'up',
      sort_by: 'diff_carton',
      sort_dir: 'desc',
    })
  })

  it('merges the advanced filters without the trend and omits them when empty', () => {
    expect(buildOverviewParams('up', '', { by: '', dir: 'asc' }, EMPTY_IMPACT_FILTERS)).toEqual({
      q: undefined,
      trend: 'up',
    })
    expect(
      buildOverviewParams('all', 'x', { by: '', dir: 'asc' }, {
        ...EMPTY_IMPACT_FILTERS,
        roles: [3],
        pct: { min: '5', max: '' },
      }),
    ).toEqual({ q: 'x', trend: undefined, part_roles: '3', pct_min: 5 })
  })
})
