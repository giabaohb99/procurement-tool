import { act, renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { DataTableColumn } from './types'
import { useTableLayout } from './use-table-layout'

type Row = { id: number }

const columns: DataTableColumn<Row>[] = [
  { key: 'code', header: 'Mã', cell: (row) => row.id, defaultPinned: true },
  { key: 'action', header: 'Thao tác', cell: () => null, stickyRight: true },
  { key: 'title', header: 'Tên', cell: () => null },
]

describe('bố cục cột cố định bên phải', () => {
  it('luôn đặt cột thao tác ở cuối dù khai báo hoặc kéo cột ở vị trí khác', () => {
    const { result } = renderHook(() => useTableLayout(columns))

    expect(result.current.visibleColumns.map((column) => column.key)).toEqual([
      'code',
      'title',
      'action',
    ])

    act(() => result.current.moveColumn('action', 'code', 'before'))

    expect(result.current.visibleColumns.map((column) => column.key)).toEqual([
      'code',
      'title',
      'action',
    ])
  })

  it('không cho ghim cột cố định bên phải sang trái', () => {
    const { result } = renderHook(() => useTableLayout(columns))

    act(() => result.current.togglePin('action'))

    expect(result.current.layout.pinnedColumns).not.toContain('action')
  })
})

// bao-CR-578: người đã lưu bố cục cũ (thứ tự cột) mà bảng vừa có cột ID tự thêm — cột mới
// thường nối vào CUỐI; cột ID phải về bìa trái, sau cột tick chọn.
describe('cột mới đặt về đầu bảng', () => {
  const STORAGE_KEY = 'test-cr577'
  const saved = (order: string[]) =>
    localStorage.setItem(`erp.table.${STORAGE_KEY}`, JSON.stringify({ columnOrder: order }))
  const idColumn: DataTableColumn<Row> = {
    key: '__row_id',
    header: 'ID',
    cell: (row) => row.id,
    placeAtStartWhenNew: true,
  }
  const plain = (key: string): DataTableColumn<Row> => ({ key, header: key, cell: () => null })

  it('puts a flagged new column first when an old saved order exists', () => {
    saved(['title', 'code'])
    const { result } = renderHook(() =>
      useTableLayout([idColumn, plain('code'), plain('title'), plain('note')], STORAGE_KEY),
    )
    expect(result.current.orderedColumns.map((column) => column.key)).toEqual([
      '__row_id',
      'title',
      'code',
      'note',
    ])
    localStorage.clear()
  })

  it('keeps the tick column ahead of it', () => {
    saved(['select', 'title'])
    const { result } = renderHook(() =>
      useTableLayout([plain('select'), idColumn, plain('title')], STORAGE_KEY),
    )
    expect(result.current.orderedColumns.map((column) => column.key)).toEqual([
      'select',
      '__row_id',
      'title',
    ])
    localStorage.clear()
  })

  it('respects where the user dragged it once it is part of the saved order', () => {
    saved(['title', '__row_id', 'code'])
    const { result } = renderHook(() =>
      useTableLayout([idColumn, plain('code'), plain('title')], STORAGE_KEY),
    )
    expect(result.current.orderedColumns.map((column) => column.key)).toEqual([
      'title',
      '__row_id',
      'code',
    ])
    localStorage.clear()
  })
})
