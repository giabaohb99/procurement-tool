import { describe, expect, it } from 'vitest'

import { EMPTY_IMPACT_FILTERS } from './packaging-impact-filters'
import {
  buildImpactUrlSearch,
  EMPTY_IMPACT_URL_STATE,
  parseImpactUrlState,
  type ImpactUrlState,
} from './packaging-impact-url-state'

const parse = (query: string) => parseImpactUrlState(new URLSearchParams(query))

describe('packaging impact URL state', () => {
  it('round-trips codes, assumed prices, dates, keyword, chip filters, sort and page', () => {
    const state: ImpactUrlState = {
      codes: ['CET0028', 'CET0051'],
      assumed: { CET0028: 4500, CET0051: 300.5 },
      dateFrom: '2026-01-01',
      dateTo: '2026-06-30',
      q: 'bohex',
      filters: {
        ...EMPTY_IMPACT_FILTERS,
        trend: 'up',
        roles: [1, 5],
        cartonQty: { min: '20', max: '' },
        diffCarton: { min: '1000', max: '2500,5' },
        warningsOnly: true,
      },
      sortBy: 'diff_carton',
      sortDir: 'desc',
      page: 3,
    }
    const query = buildImpactUrlSearch(state)
    const params = new URLSearchParams(query)
    //  Cùng tên + dạng tham số với bản v1.
    expect(params.get('codes')).toBe('CET0028,CET0051')
    expect(params.get('assumed')).toBe('CET0028:4500,CET0051:300.5')
    expect(params.get('part_roles')).toBe('1,5')
    expect(params.get('diff_carton_max')).toBe('2500.5')
    expect(params.get('warnings_only')).toBe('1')
    expect(params.get('page')).toBe('3')
    expect(parse(query)).toEqual(state)
  })

  it('writes nothing for the empty state and reads an empty query as the empty state', () => {
    expect(buildImpactUrlSearch(EMPTY_IMPACT_URL_STATE)).toBe('')
    expect(parse('')).toEqual(EMPTY_IMPACT_URL_STATE)
  })

  it('cleans bad params: unknown sort key, bad dates, bad page, foreign assumed price, junk bounds, unknown roles', () => {
    const state = parse(
      'codes=A,,A,B&assumed=A:0,C:5,B:12&date_from=2026-02-30&date_to=abc&sort_by=hack&sort_dir=desc' +
        '&page=-2&part_roles=1,9,x&trend=boom&carton_qty_min=abc&diff_bottle_max=12.5',
    )
    expect(state.codes).toEqual(['A', 'B'])
    expect(state.assumed).toEqual({ B: 12 })
    expect(state.dateFrom).toBe('')
    expect(state.dateTo).toBe('')
    expect(state.sortBy).toBe('')
    expect(state.page).toBe(1)
    expect(state.filters.roles).toEqual([1])
    expect(state.filters.trend).toBe('all')
    expect(state.filters.cartonQty).toEqual({ min: '', max: '' })
    expect(state.filters.diffBottle).toEqual({ min: '', max: '12,5' })
  })

  it('caps the code list at 500', () => {
    const codes = Array.from({ length: 600 }, (_, index) => `M${index}`).join(',')
    expect(parse(`codes=${codes}`).codes).toHaveLength(500)
  })

  it('does not write assumed prices of codes that are no longer selected', () => {
    const query = buildImpactUrlSearch({ ...EMPTY_IMPACT_URL_STATE, codes: ['A'], assumed: { A: 5, B: 7 } })
    expect(new URLSearchParams(query).get('assumed')).toBe('A:5')
  })
})
