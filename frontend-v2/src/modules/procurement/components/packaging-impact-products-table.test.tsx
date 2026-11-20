import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  usePackagingImpactTableState,
  type PackagingImpactTableState,
} from '../hooks/use-packaging-impact-table-state'
import type { PackagingImpactProduct } from '../types/packaging-cost-types'
import { PackagingImpactProductsTable } from './packaging-impact-products-table'

const product = (over: Partial<PackagingImpactProduct> = {}): PackagingImpactProduct => ({
  hh_code: 'HH0417.1',
  hh_name: 'Thuốc trừ sâu A 1 lít',
  carton_qty: 40,
  parts: [
    { role: 1, code: 'CPT0105', old: 1000, new: 1100, applied: 1100, selected: true },
    { role: 2, code: 'NAP0085', old: 300, new: 300, applied: 300, selected: false },
    { role: 3, code: '', old: null, new: null, applied: null, selected: false },
  ],
  cost_old_bottle: 1300,
  cost_new_bottle: 1400,
  cost_applied_bottle: 1400,
  diff_bottle: 100,
  pct: 7.7,
  cost_old_carton: 52000,
  cost_applied_carton: 56000,
  diff_carton: 4000,
  trend: 1,
  warnings: [{ kind: 901, role: 902 }],
  ...over,
})

function makeView(over: Partial<PackagingImpactTableState> = {}): PackagingImpactTableState {
  return {
    keyword: '',
    setKeyword: vi.fn(),
    query: '',
    sortBy: '',
    sortDir: 'asc',
    setSort: vi.fn(),
    pageSize: 100,
    setPageSize: vi.fn(),
    page: 1,
    setPage: vi.fn(),
    ...over,
  }
}

function renderTable(
  rows: PackagingImpactProduct[],
  view: PackagingImpactTableState = makeView(),
  total = rows.length,
) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <PackagingImpactProductsTable
          rows={rows}
          total={total}
          isLoading={false}
          isError={false}
          view={view}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/** Dùng hook thật để thử ô tìm (trạng thái nằm ở màn, bảng chỉ điều khiển qua `view`). */
function TableWithRealState({ rows }: { rows: PackagingImpactProduct[] }) {
  const view = usePackagingImpactTableState([])
  return (
    <PackagingImpactProductsTable
      rows={rows}
      total={rows.length}
      isLoading={false}
      isError={false}
      view={view}
    />
  )
}

beforeEach(() => localStorage.clear())

describe('PackagingImpactProductsTable', () => {
  it('renders a missing bottle cost as a real dash element, not an empty cell', () => {
    renderTable([
      product({
        cost_old_bottle: null,
        cost_applied_bottle: null,
        diff_bottle: null,
        diff_carton: null,
      }),
    ])
    const row = screen.getByText('HH0417.1').closest('tr') as HTMLTableRowElement
    expect(within(row).getAllByText('—').length).toBeGreaterThanOrEqual(4)
  })

  it('shows "old → new" only on components whose price changed', () => {
    renderTable([product()])
    expect(screen.getByText('1.000 →')).toBeInTheDocument()
    expect(screen.queryByText('300 →')).not.toBeInTheDocument()
  })

  it('joins warning labels with the component role in the note column', () => {
    renderTable([product()])
    expect(screen.getByText('Mã 901: Mã 902')).toBeInTheDocument()
  })

  it('renders the rows in the order the server sent, never re-sorting or re-filtering a page', async () => {
    const user = userEvent.setup()
    const view = makeView()
    renderTable(
      [product({ hh_code: 'HH0999', hh_name: 'Z' }), product({ hh_code: 'HH0001', hh_name: 'A' })],
      view,
    )
    await user.click(screen.getByText('Mã HH'))
    expect(view.setSort).toHaveBeenCalledWith('hh_code', 'asc')
    const codes = screen.getAllByText(/^HH\d{4}$/).map((el) => el.textContent)
    expect(codes).toEqual(['HH0999', 'HH0001'])
  })

  it('numbers rows from the page offset and takes the total from the server, not from the page rows', () => {
    renderTable([product({ hh_code: 'HH0101' })], makeView({ page: 3, pageSize: 100 }), 4321)
    const row = screen.getByText('HH0101').closest('tr') as HTMLTableRowElement
    expect(within(row).getByText('201')).toBeInTheDocument()
    expect(screen.getByText(/4\.321/)).toBeInTheDocument()
  })

  it('reports typed keywords to the screen and tells "no match" from "nothing selected"', async () => {
    const user = userEvent.setup()
    render(
      <QueryClientProvider client={new QueryClient()}>
        <MemoryRouter>
          <TableWithRealState rows={[]} />
        </MemoryRouter>
      </QueryClientProvider>,
    )
    expect(screen.getByText('Không có sản phẩm nào dùng các mã đã chọn.')).toBeInTheDocument()
    await user.type(screen.getByLabelText('Tìm sản phẩm'), 'khong co')
    expect(await screen.findByText('Không có sản phẩm khớp từ khóa.')).toBeInTheDocument()
    await user.clear(screen.getByLabelText('Tìm sản phẩm'))
    expect(await screen.findByText('Không có sản phẩm nào dùng các mã đã chọn.')).toBeInTheDocument()
  })
})
