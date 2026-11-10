// duoc-CR-744 — sắp xếp trên trình duyệt cho các bảng nhỏ đã tải đủ dòng của Tra cứu thị trường.
import { act, renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { useClientTableSort } from './use-client-table-sort'

interface Row {
  id: number
  name: string | null
  price: number | string | null
}

const ROWS: Row[] = [
  { id: 1, name: 'Beta', price: 5 },
  { id: 2, name: null, price: 0 },
  { id: 3, name: 'alpha', price: null },
  { id: 4, name: '   ', price: '12.5' },
  { id: 5, name: 'Alpha', price: '12.25' },
]
const getValue = (key: string, row: Row) => (key === 'name' ? row.name : key === 'price' ? row.price : null)
const ids = (rows: Row[] | undefined) => rows?.map((row) => row.id)

describe('useClientTableSort', () => {
  it('keeps the original order until a column is picked', () => {
    const { result } = renderHook(() => useClientTableSort(ROWS, getValue))
    expect(ids(result.current.rows)).toEqual([1, 2, 3, 4, 5])
    expect(result.current.sortBy).toBe('')
  })

  it('puts blank cells (null, empty and whitespace-only text) LAST in both directions', () => {
    const { result } = renderHook(() => useClientTableSort(ROWS, getValue))
    act(() => result.current.onSortChange('name', 'asc'))
    expect(ids(result.current.rows)?.slice(-2).sort()).toEqual([2, 4])
    act(() => result.current.onSortChange('name', 'desc'))
    expect(ids(result.current.rows)?.slice(-2).sort()).toEqual([2, 4])
  })

  it('treats a numeric 0 as a real value, not as blank, and compares numeric strings as numbers', () => {
    const { result } = renderHook(() => useClientTableSort(ROWS, getValue))
    act(() => result.current.onSortChange('price', 'asc'))
    //  0 < 5 < "12.25" < "12.5": chuỗi số so theo SỐ (so theo chữ thì "12.5" đứng sau "12.25" chỉ do tình cờ),
    //  số 0 là giá trị thật nên đứng đầu; null xuống cuối.
    expect(ids(result.current.rows)).toEqual([2, 1, 5, 4, 3])
    act(() => result.current.onSortChange('price', 'desc'))
    expect(ids(result.current.rows)).toEqual([4, 5, 1, 2, 3])
  })

  it('keeps equal values in their original order so rows do not swap on every click', () => {
    const rows: Row[] = [
      { id: 1, name: 'Same', price: 1 },
      { id: 2, name: 'same', price: 1 },
      { id: 3, name: 'SAME', price: 1 },
    ]
    const { result } = renderHook(() => useClientTableSort(rows, getValue))
    act(() => result.current.onSortChange('name', 'asc'))
    expect(ids(result.current.rows)).toEqual([1, 2, 3])
    act(() => result.current.onSortChange('name', 'desc'))
    expect(ids(result.current.rows)).toEqual([1, 2, 3])
  })

  it('returns to the original order on the empty key and passes undefined / empty input through', () => {
    const { result } = renderHook(() => useClientTableSort(ROWS, getValue))
    act(() => result.current.onSortChange('price', 'desc'))
    act(() => result.current.onSortChange('', 'asc'))
    expect(ids(result.current.rows)).toEqual([1, 2, 3, 4, 5])
    expect(result.current.sortDir).toBe('asc')

    const loading = renderHook(() => useClientTableSort<Row>(undefined, getValue))
    act(() => loading.result.current.onSortChange('name', 'asc'))
    expect(loading.result.current.rows).toBeUndefined()
    const empty = renderHook(() => useClientTableSort<Row>([], getValue))
    act(() => empty.result.current.onSortChange('name', 'asc'))
    expect(empty.result.current.rows).toEqual([])
  })
})
