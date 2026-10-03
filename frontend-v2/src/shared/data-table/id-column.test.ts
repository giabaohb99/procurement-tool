import { describe, expect, it } from 'vitest'

import {
  ID_COLUMN_KEY,
  leadingColumnCount,
  readRowId,
  shouldShowIdColumn,
  withIdColumn,
} from './id-column'
import type { DataTableColumn } from './types'

// bao-CR-578 — mọi bảng danh sách tự có cột «ID» ở bìa trái (đại ca chốt 03/10/2026).

type Row = { id?: unknown; name: string }

const col = (key: string): DataTableColumn<Row> => ({ key, header: key, cell: (row) => row.name })

describe('readRowId', () => {
  it('reads only finite numeric ids', () => {
    expect(readRowId({ id: 12 })).toBe(12)
    expect(readRowId({ id: 0 })).toBe(0)
    for (const row of [null, undefined, 'x', 5, {}, { id: '12' }, { id: NaN }, { id: Infinity }, { id: null }]) {
      expect(readRowId(row)).toBeNull()
    }
  })
})

describe('shouldShowIdColumn', () => {
  const rows: Row[] = [{ id: 1, name: 'a' }]

  it('is on by default for rows carrying a numeric id', () => {
    expect(shouldShowIdColumn([col('code')], rows, true)).toBe(true)
  })

  it('stays on while loading or empty so the table does not jump', () => {
    expect(shouldShowIdColumn([col('code')], undefined, true)).toBe(true)
    expect(shouldShowIdColumn([col('code')], [], true)).toBe(true)
  })

  it('is off when the screen opts out or already declares its own id column', () => {
    expect(shouldShowIdColumn([col('code')], rows, false)).toBe(false)
    expect(shouldShowIdColumn([col('id'), col('code')], rows, true)).toBe(false)
    expect(shouldShowIdColumn([col(ID_COLUMN_KEY)], rows, true)).toBe(false)
  })

  it('is off for grouped rows without any numeric id instead of a column of dashes', () => {
    expect(shouldShowIdColumn([col('group')], [{ name: 'x' }, { id: 'A', name: 'y' }], true)).toBe(false)
  })

  it('a single row with an id is enough to keep the column', () => {
    expect(shouldShowIdColumn([col('code')], [{ name: 'x' }, { id: 3, name: 'y' }], true)).toBe(true)
  })
})

describe('withIdColumn', () => {
  it('puts the id column first', () => {
    const keys = withIdColumn([col('code'), col('name')], true).map((column) => column.key)
    expect(keys).toEqual([ID_COLUMN_KEY, 'code', 'name'])
  })

  it('never jumps ahead of the tick column', () => {
    const keys = withIdColumn([col('select'), col('code')], true).map((column) => column.key)
    expect(keys).toEqual(['select', ID_COLUMN_KEY, 'code'])
  })

  it('returns the very same array when hidden so layouts memoised on it stay stable', () => {
    const columns = [col('code')]
    expect(withIdColumn(columns, false)).toBe(columns)
  })

  it('renders the id, or nothing for a row without one', () => {
    const idColumn = withIdColumn([col('code')], true)[0]
    expect(idColumn.cell({ id: 42, name: 'x' })).toBe(42)
    expect(idColumn.cell({ name: 'x' })).toBe('')
    expect(idColumn.placeAtStartWhenNew).toBe(true)
  })

  it('works on an empty column list', () => {
    expect(withIdColumn<Row>([], true).map((column) => column.key)).toEqual([ID_COLUMN_KEY])
  })
})

describe('leadingColumnCount', () => {
  it('counts only the tick columns at the very start', () => {
    expect(leadingColumnCount([])).toBe(0)
    expect(leadingColumnCount(['code', 'select'])).toBe(0)
    expect(leadingColumnCount(['select', 'code'])).toBe(1)
  })
})
