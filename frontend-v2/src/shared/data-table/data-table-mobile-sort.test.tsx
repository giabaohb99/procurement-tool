import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { DataTable } from './data-table'
import { DataTableMobileSort } from './data-table-mobile-sort'
import type { DataTableColumn } from './types'

type Row = { id: number }
const columns: DataTableColumn<Row>[] = [
  { key: 'code', header: 'Mã', sortable: true, cell: () => null },
  { key: 'p1_date', header: 'Ngày mua', group: 'Lần 1', sortable: true, sortDescFirst: true, cell: () => null },
  { key: 'note', header: 'Ghi chú', cell: () => null },
]

describe('DataTableMobileSort', () => {
  it('names the active sort column (with its group) and flips the direction', () => {
    const onSortChange = vi.fn()
    render(<DataTableMobileSort columns={columns} sortBy="p1_date" sortDir="desc" onSortChange={onSortChange} />)
    expect(screen.getByRole('combobox', { name: 'Xếp theo: Lần 1 · Ngày mua' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Đang xếp giảm dần/ }))
    expect(onSortChange).toHaveBeenCalledWith('p1_date', 'asc')
  })

  it('hides the direction button when nothing is sorted, and renders nothing without sortable columns', () => {
    const { rerender, container } = render(
      <DataTableMobileSort columns={columns} sortBy="" onSortChange={vi.fn()} />,
    )
    expect(screen.getByRole('combobox', { name: 'Xếp theo' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Đang xếp/ })).not.toBeInTheDocument()
    rerender(<DataTableMobileSort columns={[columns[2]]} sortBy="" onSortChange={vi.fn()} />)
    expect(container).toBeEmptyDOMElement()
  })
})

describe('DataTable card mode with mobileSort', () => {
  afterEach(() => vi.unstubAllGlobals())

  function renderTable(mobileSort: boolean) {
    //  Khổ hẹp: `useIsMobile` hỏi `matchMedia` — giả "khớp" để bảng chuyển sang thẻ.
    vi.stubGlobal('matchMedia', (query: string) => ({
      matches: true,
      media: query,
      addEventListener: () => {},
      removeEventListener: () => {},
    }))
    render(
      <QueryClientProvider client={new QueryClient()}>
        <DataTable
          columns={columns}
          rows={[{ id: 1 }]}
          getRowId={(row) => row.id}
          mobileCard={(row) => <span>Thẻ {row.id}</span>}
          mobileSort={mobileSort}
          sortBy=""
          onSortChange={vi.fn()}
        />
      </QueryClientProvider>,
    )
  }

  it('shows the "Xếp theo" control instead of column headers', () => {
    renderTable(true)
    expect(screen.getByText('Thẻ 1')).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: 'Xếp theo' })).toBeInTheDocument()
  })

  it('stays opt-in: no control without the prop', () => {
    renderTable(false)
    expect(screen.queryByRole('combobox', { name: 'Xếp theo' })).not.toBeInTheDocument()
  })
})
