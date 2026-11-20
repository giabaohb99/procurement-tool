import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'

import { DataTable } from './data-table'
import type { DataTableColumn } from './types'

interface Row {
  id: number
}

const col = (key: string, group?: string, extra: Partial<DataTableColumn<Row>> = {}): DataTableColumn<Row> => ({
  key,
  header: key.toUpperCase(),
  cell: () => key,
  width: 100,
  group,
  ...extra,
})

function build(columns: DataTableColumn<Row>[], storageKey?: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const { container } = render(
    <QueryClientProvider client={client}>
      <DataTable
        columns={columns}
        rows={[{ id: 1 }]}
        getRowId={(r) => r.id}
        storageKey={storageKey}
        idColumn={false}
      />
    </QueryClientProvider>,
  )
  return container.querySelector('table') as HTMLTableElement
}

const groupCells = (table: HTMLTableElement) =>
  [...table.querySelectorAll<HTMLTableCellElement>('thead tr:first-child th')].map((th) => [
    th.textContent,
    th.colSpan,
  ])

beforeEach(() => localStorage.clear())

describe('DataTable — nhóm cột (group)', () => {
  it('draws no extra header row when no column declares a group (backward compatible)', () => {
    const table = build([col('a'), col('b')])
    expect(table.querySelectorAll('thead tr')).toHaveLength(1)
  })

  it('draws a group row above the column names with colSpan per run of the same group', () => {
    const table = build([col('code', 'Thông tin'), col('name', 'Thông tin'), col('d1', 'Lần 1'), col('p1', 'Lần 1'), col('avg', 'Giá TB')])
    expect(table.querySelectorAll('thead tr')).toHaveLength(2)
    expect(groupCells(table)).toEqual([
      ['Thông tin', 2],
      ['Lần 1', 2],
      ['Giá TB', 1],
    ])
    // the column-name row stays the second row, one cell per column
    expect(table.querySelectorAll('thead tr:nth-child(2) th')).toHaveLength(5)
  })

  it('never tints group columns and draws a thin group divider in the header only', () => {
    const table = build([col('code', 'Thông tin'), col('d1', 'Lần 1'), col('p1', 'Lần 1'), col('avg', 'Giá TB')])
    const head = [...table.querySelectorAll<HTMLElement>('thead tr:nth-child(2) th')]
    const body = [...table.querySelectorAll<HTMLElement>('tbody tr:first-child td')]
    // Owner (20/11): a two-tone header looked patchy, and a per-group body tint on top of the row zebra made a checkered
    // pattern that was hard to read — groups are now shown by the header row and its thin divider only, no tint anywhere.
    expect([...head, ...body].some((el) => el.style.backgroundImage !== '')).toBe(false)
    // Group divider: thin 1px line on the header of the last column of Thông tin and of Lần 1, never the heavy 2px
    // `dividerAfter` line, and nothing in the body (owner 20/11: the tint alone separates groups there).
    const groupLine = (el: HTMLElement) => el.className.includes('var(--foreground)_28%')
    const heavy = (el: HTMLElement) => el.className.includes('inset_-2px_0_0_0_var(--muted-foreground)')
    expect(head.map(groupLine)).toEqual([true, false, true, false])
    expect([...head, ...body].some(heavy)).toBe(false)
    expect(body.map(groupLine)).toEqual([false, false, false, false])
  })

  it('colours only the header of a group with groupTone, one chart colour per tone, and never the body', () => {
    const table = build([
      col('code', 'Thông tin'),
      col('d1', 'Lần 1', { groupTone: 0 }),
      col('p1', 'Lần 1', { groupTone: 0 }),
      col('d2', 'Lần 2', { groupTone: 1 }),
      col('d5', 'Lần 5', { groupTone: 4 }),
    ])
    const groupRow = [...table.querySelectorAll<HTMLElement>('thead tr:first-child th')]
    const head = [...table.querySelectorAll<HTMLElement>('thead tr:nth-child(2) th')]
    const body = [...table.querySelectorAll<HTMLElement>('tbody tr:first-child td')]
    const tokenOf = (el: HTMLElement) => /--chart-(\d)/.exec(el.style.backgroundColor)?.[1] ?? null
    // Thông tin has no tone; Lần 1 → chart-1, Lần 2 → chart-2, Lần 5 wraps around the 4 theme colours back to chart-1.
    expect(groupRow.map(tokenOf)).toEqual([null, '1', '2', '1'])
    expect(head.map(tokenOf)).toEqual([null, '1', '1', '2', '1'])
    // Owner (20/11): the body stays white + row zebra, a tinted body made a hard-to-read checkered pattern.
    expect(body.every((td) => td.style.backgroundColor === '' && td.style.backgroundImage === '')).toBe(true)
  })

  it('shrinks a group when one of its columns is hidden and drops it when none is left', () => {
    localStorage.setItem(
      'erp.table.dt-groups',
      JSON.stringify({ hiddenColumns: ['d1', 'p1'], columnWidths: {}, columnOrder: [], pinnedColumns: [], columnColors: {} }),
    )
    const table = build([col('code', 'Thông tin'), col('d1', 'Lần 1'), col('p1', 'Lần 1'), col('avg', 'Giá TB')], 'dt-groups')
    expect(groupCells(table)).toEqual([
      ['Thông tin', 1],
      ['Giá TB', 1],
    ])
  })

  it('keeps an ungrouped column in an unlabeled cell', () => {
    const table = build([col('a'), col('b', 'Nhóm')])
    expect(groupCells(table)).toEqual([
      ['', 1],
      ['Nhóm', 1],
    ])
  })

  it('writes the group label once when pinning splits the group', () => {
    localStorage.setItem(
      'erp.table.dt-pin',
      JSON.stringify({ hiddenColumns: [], columnWidths: {}, columnOrder: [], pinnedColumns: ['code'], columnColors: {} }),
    )
    const table = build([col('code', 'Thông tin'), col('name', 'Thông tin'), col('d1', 'Lần 1')], 'dt-pin')
    expect(groupCells(table)).toEqual([
      ['', 1],
      ['Thông tin', 1],
      ['Lần 1', 1],
    ])
  })

  it('declares every column width in a colgroup (table-fixed would split widths equally from the colSpan row)', () => {
    const table = build([col('a', 'G', { width: 120 }), col('b', 'G', { width: 300 }), col('c', 'H', { width: 70 })])
    const widths = [...table.querySelectorAll<HTMLElement>('colgroup col')].map((c) => c.style.width)
    expect(widths).toEqual(['120px', '300px', '70px'])
  })

  it('adds no colgroup to a table without groups', () => {
    expect(build([col('a'), col('b')]).querySelector('colgroup')).toBeNull()
  })
})
