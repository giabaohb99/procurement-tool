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

// bao-CR-705: thêm cột ẩn sẵn vào bảng đã phát hành — luật cũ (docs/ui/table.md §4) bật sẵn cột đó
// trước mặt mọi người đã từng lưu bố cục, nên danh sách ĐMH thêm chục cột phụ là vỡ bảng của họ.
describe('cột mới ẩn sẵn trước mặt người đã lưu bố cục', () => {
  const KEY = 'test-cr705'
  const base: DataTableColumn<Row>[] = [
    { key: 'code', header: 'Mã', cell: (row) => row.id },
    { key: 'title', header: 'Tên', cell: () => null },
  ]
  const withNew: DataTableColumn<Row>[] = [
    ...base,
    { key: 'shown_new', header: 'Mới hiện', cell: () => null },
    {
      key: 'hidden_new',
      header: 'Mới ẩn',
      cell: () => null,
      defaultHidden: true,
      hiddenForOlderLayouts: true,
    },
  ]
  const keysOf = (cols: { key: string }[]) => cols.map((c) => c.key)
  const save = (layout: object) =>
    localStorage.setItem(`erp.table.${KEY}`, JSON.stringify(layout))

  it('hides a new defaultHidden column for a layout saved with knownColumns', () => {
    localStorage.clear()
    save({ hiddenColumns: [], columnWidths: {}, knownColumns: ['code', 'title'] })
    const { result } = renderHook(() => useTableLayout(withNew, KEY))
    expect(keysOf(result.current.visibleColumns)).toEqual(['code', 'title', 'shown_new'])
  })

  it('hides a flagged column for a legacy layout that never mentioned it', () => {
    localStorage.clear()
    //  Bản lưu kiểu cũ: không có knownColumns, người dùng mới kéo giãn cột "Tên".
    save({ hiddenColumns: [], columnWidths: { title: 220 } })
    const { result } = renderHook(() => useTableLayout(withNew, KEY))
    expect(keysOf(result.current.visibleColumns)).toEqual(['code', 'title', 'shown_new'])
  })

  it('keeps an old unflagged defaultHidden column exactly as a legacy layout showed it', () => {
    localStorage.clear()
    const legacy: DataTableColumn<Row>[] = [
      ...base,
      { key: 'note', header: 'Ghi chú', cell: () => null, defaultHidden: true },
    ]
    save({ hiddenColumns: [], columnWidths: {} })
    const { result } = renderHook(() => useTableLayout(legacy, KEY))
    expect(keysOf(result.current.visibleColumns)).toEqual(['code', 'title', 'note'])
  })

  it('does not hide again a new column the user switched on', () => {
    localStorage.clear()
    save({ hiddenColumns: [], columnWidths: {}, knownColumns: ['code', 'title'] })
    const first = renderHook(() => useTableLayout(withNew, KEY))
    act(() => first.result.current.toggleColumn('hidden_new'))
    first.unmount()
    const again = renderHook(() => useTableLayout(withNew, KEY))
    expect(keysOf(again.result.current.visibleColumns)).toContain('hidden_new')
  })

  it('reset brings back the default set and drops dragged widths', () => {
    localStorage.clear()
    save({ hiddenColumns: ['title'], columnWidths: { code: 300 }, knownColumns: ['code', 'title'] })
    const { result } = renderHook(() => useTableLayout(withNew, KEY))
    act(() => result.current.resetLayout())
    expect(keysOf(result.current.visibleColumns)).toEqual(['code', 'title', 'shown_new'])
    expect(result.current.layout.columnWidths).toEqual({})
  })

  it('treats a corrupt knownColumns value as a legacy layout instead of crashing', () => {
    localStorage.clear()
    save({ hiddenColumns: [], columnWidths: {}, knownColumns: 'code,title' })
    const { result } = renderHook(() => useTableLayout(withNew, KEY))
    expect(keysOf(result.current.visibleColumns)).toEqual(['code', 'title', 'shown_new'])
    localStorage.clear()
  })
})
