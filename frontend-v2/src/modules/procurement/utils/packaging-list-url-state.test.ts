import { describe, expect, it } from 'vitest'

import {
  buildLastPricesUrlSearch,
  buildPriceListUrlSearch,
  DEFAULT_LAST_PRICES_FILTERS,
  parseLastPricesUrlState,
  parsePriceListUrlState,
  type LastPricesUrlState,
  type PriceListUrlState,
} from './packaging-list-url-state'

const parsePriceList = (query: string) => parsePriceListUrlState(new URLSearchParams(query))
const parseLast = (query: string) => parseLastPricesUrlState(new URLSearchParams(query))

describe('Bảng giá VTBB URL state', () => {
  it('round-trips filters, date range, sort, page and page size with API param names', () => {
    const state: PriceListUrlState = {
      filters: { q: 'nắp', group: 'Nắp', scope: 'all' },
      from: '2026-01-01',
      to: '2026-06-30',
      sortBy: 'pct',
      sortDir: 'desc',
      page: 3,
      pageSize: 20,
    }
    const query = buildPriceListUrlSearch(state)
    const params = new URLSearchParams(query)
    expect(params.get('q')).toBe('nắp')
    expect(params.get('group')).toBe('Nắp')
    expect(params.get('scope')).toBe('all')
    expect(params.get('date_from')).toBe('2026-01-01')
    expect(params.get('date_to')).toBe('2026-06-30')
    expect(params.get('sort_by')).toBe('pct')
    expect(params.get('sort_dir')).toBe('desc')
    expect(params.get('page')).toBe('3')
    expect(params.get('page_size')).toBe('20')
    expect(parsePriceList(query)).toEqual(state)
  })

  it('writes nothing for the default state', () => {
    const state = parsePriceList('')
    expect(state).toEqual({
      filters: { q: '', group: '', scope: 'bom' },
      from: '',
      to: '',
      sortBy: '',
      sortDir: 'asc',
      page: 1,
      pageSize: 50,
    })
    expect(buildPriceListUrlSearch(state)).toBe('')
  })

  it('drops bad params', () => {
    const state = parsePriceList(
      'scope=zzz&date_from=2026-13-40&date_to=abc&sort_by=hack&sort_dir=desc&page=-4&page_size=7',
    )
    expect(state.filters.scope).toBe('bom')
    expect(state.from).toBe('')
    expect(state.to).toBe('')
    expect(state.sortBy).toBe('')
    expect(state.sortDir).toBe('asc')
    expect(state.page).toBe(1)
    expect(state.pageSize).toBe(50)
  })

  it('drops an inverted date range and cuts over-long text', () => {
    const state = parsePriceList(`date_from=2026-05-02&date_to=2026-05-01&q=${'a'.repeat(300)}`)
    expect(state.from).toBe('')
    expect(state.to).toBe('')
    expect(state.filters.q).toHaveLength(100)
  })
})

describe('Giá mua gần nhất URL state', () => {
  it('round-trips every filter, sort, page and page size', () => {
    const state: LastPricesUrlState = {
      filters: {
        q: 'chai',
        group: 'Chai',
        n: 10,
        scope: 'all',
        suppliers: ['NCC01', 'NCC02'],
        from: '2026-02-01',
        to: '2026-03-01',
        trend: 'up',
        minPct: 7.5,
        onlyPriced: false,
        bomOnly: true,
        showQty: true,
      },
      sortBy: 'p7_price',
      sortDir: 'desc',
      page: 2,
      pageSize: 100,
    }
    const query = buildLastPricesUrlSearch(state)
    const params = new URLSearchParams(query)
    expect(params.getAll('supplier')).toEqual(['NCC01', 'NCC02'])
    expect(params.get('n')).toBe('10')
    expect(params.get('min_pct')).toBe('7.5')
    expect(params.get('only_priced')).toBe('0')
    expect(params.get('bom_only')).toBe('1')
    expect(params.get('show_qty')).toBe('1')
    expect(params.get('trend')).toBe('up')
    expect(parseLast(query)).toEqual(state)
  })

  it('writes nothing for the default state (only_priced on, n = 5)', () => {
    const state = parseLast('')
    expect(state.filters).toEqual(DEFAULT_LAST_PRICES_FILTERS)
    expect(buildLastPricesUrlSearch(state)).toBe('')
  })

  it('accepts true / false spellings for flags', () => {
    const filters = parseLast('only_priced=false&bom_only=true&show_qty=1').filters
    expect(filters.onlyPriced).toBe(false)
    expect(filters.bomOnly).toBe(true)
    expect(filters.showQty).toBe(true)
  })

  it('drops bad params', () => {
    const state = parseLast(
      'n=4&trend=missing&min_pct=-3&only_priced=maybe&sort_by=evil&page=0&page_size=999&date_from=2026-02-30',
    )
    expect(state.filters.n).toBe(5)
    expect(state.filters.trend).toBe('all')
    expect(state.filters.minPct).toBe(0)
    expect(state.filters.onlyPriced).toBe(true)
    expect(state.filters.from).toBe('')
    expect(state.sortBy).toBe('')
    expect(state.page).toBe(1)
    expect(state.pageSize).toBe(50)
  })

  it('drops a sort slot beyond the shown purchase count and blank / duplicate suppliers', () => {
    expect(parseLast('n=3&sort_by=p4_price').sortBy).toBe('')
    expect(parseLast('n=3&sort_by=p3_date&sort_dir=desc').sortBy).toBe('p3_date')
    expect(parseLast('sort_by=p11_price').sortBy).toBe('')
    expect(parseLast('supplier=A&supplier=&supplier=A&supplier=B').filters.suppliers).toEqual(['A', 'B'])
  })
})
