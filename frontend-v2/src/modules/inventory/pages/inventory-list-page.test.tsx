import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ListParams } from '@/shared/types/api'
import { InventoryListPage } from './inventory-list-page'

/**
 * duoc-CR-744 — bấm tiêu đề cột Tồn kho phải gửi `sort_by` lên server. Trước đây màn không có sắp xếp nào
 * (`DataTable` chưa nối, `/api/inventory` không nhận tham số), nên phải tải về rồi đọc mắt.
 */
const calls: ListParams[] = []

vi.mock('../hooks/use-inventory', () => ({
  useInventoryItems: (params: ListParams) => {
    calls.push(params)
    return { data: { total: 0, items: [] }, isLoading: false, isError: false }
  },
}))
vi.mock('../hooks/use-inventory-catalog', () => ({
  useWarehouseOptions: () => ({ data: { items: [] } }),
  useItemGroupOptions: () => ({ data: { items: [] } }),
}))
vi.mock('@/modules/hr/hooks/use-companies', () => ({
  useCompanies: () => ({ data: { total: 0, items: [] } }),
}))
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAccess: () => true }),
}))
vi.mock('../components/inventory-adjust-dialog', () => ({ InventoryAdjustDialog: () => null }))
vi.mock('../components/inventory-detail-dialog', () => ({ InventoryDetailDialog: () => null }))

function build(url = '/inventory/stock') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <InventoryListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const header = (text: string) => screen.getByText(text, { selector: 'thead span' })
const last = () => calls[calls.length - 1]

beforeEach(() => {
  calls.length = 0
})

describe('InventoryListPage — sắp xếp cột (duoc-CR-744)', () => {
  it('sends the column key as sort_by for every data column', async () => {
    const user = userEvent.setup()
    build()

    const cases: [string, string][] = [
      ['Công ty', 'company'],
      ['Kho', 'warehouse_code'],
      ['Mã SP', 'product_code'],
      ['Tên sản phẩm', 'product_name'],
      ['ĐVT', 'unit'],
      ['Tồn hiện tại', 'qty'],
      ['Đơn giá BQ', 'avg_cost'],
      ['Giá trị tồn', 'value'],
    ]
    for (const [text, key] of cases) {
      await user.click(header(text))
      expect(last().sort_by, text).toBe(key)
    }
  })

  it('asks for the biggest first on the first click of quantity and money columns', async () => {
    const user = userEvent.setup()
    build()

    await user.click(header('Giá trị tồn'))
    expect(last()).toMatchObject({ sort_by: 'value', sort_dir: 'desc' })
    await user.click(header('Mã SP'))
    expect(last()).toMatchObject({ sort_by: 'product_code', sort_dir: 'asc' })
  })

  it('cycles asc -> desc -> off and drops both params; no sort by default', async () => {
    const user = userEvent.setup()
    build()

    expect(last().sort_by).toBeUndefined()
    await user.click(header('Kho'))
    expect(last()).toMatchObject({ sort_by: 'warehouse_code', sort_dir: 'asc', page: 1 })
    await user.click(header('Kho'))
    expect(last()).toMatchObject({ sort_by: 'warehouse_code', sort_dir: 'desc' })
    await user.click(header('Kho'))
    expect(last().sort_by).toBeUndefined()
    expect(last().sort_dir).toBeUndefined()
  })

  it('keeps the filters and goes back to page 1 when the sort changes', async () => {
    const user = userEvent.setup()
    build('/inventory/stock?qty_status=negative_stock')

    await user.click(header('Tồn hiện tại'))
    expect(last()).toMatchObject({ qty_status: 'negative_stock', sort_by: 'qty', page: 1 })
  })
})
