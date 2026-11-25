// duoc-CR-784 — màn Tổng hợp theo sản phẩm: chip xu hướng kèm số đếm, lọc / tìm / xếp đi tới máy chủ, mã bấm được sang
// Lịch sử mua hàng, Xuất Excel theo đúng bộ lọc (không kèm trang) và gác theo quyền xuất.
// Chặn ở tầng `@/core/api` (luật testing.md) để bắt được đúng đường API màn gọi đi.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'

import type {
  PackagingImpactProduct,
  PackagingOverviewResult,
} from '../types/packaging-cost-types'
import { PackagingProductOverviewPage } from './packaging-product-overview-page'

const COUNTS = { all: 1000, up: 263, down: 322, flat: 415, missing: 0 }
const calls: { url: string; params?: Record<string, unknown> }[] = []
const downloads: { url: string; params?: Record<string, unknown> }[] = []
let canExport = true

const product = (over: Partial<PackagingImpactProduct> = {}): PackagingImpactProduct => ({
  fg_code: 'HH0417.1',
  fg_name: 'Thuốc trừ sâu A 1 lít',
  carton_qty: 40,
  parts: [
    { role: 1, code: 'CPT0105', old: 1000, new: 1100, applied: 1100, selected: false },
    { role: 2, code: 'NAP0085', old: 300, new: 300, applied: 300, selected: false },
  ],
  cost_old_bottle: 1300,
  cost_new_bottle: 1400,
  cost_applied_bottle: 1400,
  diff_bottle: 100,
  pct: 0.0769,
  cost_old_carton: 52000,
  cost_applied_carton: 56000,
  diff_carton: 4000,
  trend: 1,
  warnings: [],
  ...over,
})

let result: PackagingOverviewResult = { items: [], total: 0, counts: COUNTS }

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    apiGet: async (url: string, config?: { params?: Record<string, unknown> }) => {
      calls.push({ url, params: config?.params })
      return result
    },
    downloadFile: async (url: string, _name: string, params?: Record<string, unknown>) => {
      downloads.push({ url, params })
    },
  }
})

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (_entity: string, action: string) => (action === 'export' ? canExport : true),
    canAccess: () => true,
  }),
}))

function build() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <PackagingProductOverviewPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const lastParams = () => calls[calls.length - 1]?.params

beforeEach(() => {
  calls.length = 0
  downloads.length = 0
  canExport = true
  localStorage.clear()
  result = {
    items: [
      product(),
      product({ fg_code: 'HH0500', fg_name: 'Không có giá chai', trend: 4, cost_old_bottle: null,
        cost_new_bottle: null, cost_applied_bottle: null, diff_bottle: null, diff_carton: null, pct: null }),
    ],
    total: 2,
    counts: COUNTS,
  }
})

describe('PackagingProductOverviewPage', () => {
  it('shows the five trend chips with counts from the server and no KPI cards', async () => {
    build()
    expect(await screen.findByRole('button', { name: 'Tất cả (1.000)' })).toHaveAttribute('aria-pressed', 'true')
    for (const name of ['Tăng (263)', 'Giảm (322)', 'Không đổi (415)', 'Chưa có giá (0)']) {
      expect(screen.getByRole('button', { name })).toHaveAttribute('aria-pressed', 'false')
    }
    expect(calls[0].url).toBe('/api/packaging-cost/product-overview')
    expect(calls[0].params).toMatchObject({ page: 1, page_size: 100 })
    expect(calls[0].params?.trend).toBeUndefined()
  })

  it('renders rows with trend text, signed differences and links to the purchase history', async () => {
    build()
    const row = (await screen.findByText('Thuốc trừ sâu A 1 lít')).closest('tr') as HTMLTableRowElement
    expect(within(row).getByText('Tăng')).toBeInTheDocument()
    expect(within(row).getByText('+100')).toBeInTheDocument()
    expect(within(row).getByText('+7,7%')).toBeInTheDocument()
    expect(within(row).getByRole('link', { name: 'HH0417.1' })).toHaveAttribute(
      'href',
      '/procurement/packaging-cost/history?fg=HH0417.1',
    )
    expect(within(row).getByRole('link', { name: 'CPT0105' })).toHaveAttribute(
      'href',
      '/procurement/packaging-cost/history?codes=CPT0105',
    )
    const missing = screen.getByText('Không có giá chai').closest('tr') as HTMLTableRowElement
    expect(within(missing).getByText('Chưa có giá')).toBeInTheDocument()
    expect(within(missing).getAllByText('—').length).toBeGreaterThanOrEqual(3)
  })

  it('sends the chosen trend chip to the server and goes back to page 1', async () => {
    const user = userEvent.setup()
    build()
    await user.click(await screen.findByRole('button', { name: 'Tăng (263)' }))
    await waitFor(() => expect(lastParams()).toMatchObject({ trend: 'up', page: 1 }))
    expect(screen.getByRole('button', { name: 'Tăng (263)' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('sends the debounced keyword and the clicked sort column', async () => {
    const user = userEvent.setup()
    build()
    await user.type(await screen.findByLabelText('Tìm sản phẩm'), 'b07')
    await waitFor(() => expect(lastParams()).toMatchObject({ q: 'b07' }))
    await user.click(screen.getByText('Chênh /thùng'))
    await waitFor(() =>
      expect(lastParams()).toMatchObject({ q: 'b07', sort_by: 'diff_carton', sort_dir: 'desc' }),
    )
  })

  it('exports with the same filters and order but without the page', async () => {
    const user = userEvent.setup()
    build()
    await user.click(await screen.findByRole('button', { name: 'Giảm (322)' }))
    await waitFor(() => expect(lastParams()).toMatchObject({ trend: 'down' }))
    await user.click(screen.getByRole('button', { name: /Xuất Excel/ }))
    await waitFor(() => expect(downloads).toHaveLength(1))
    expect(downloads[0].url).toBe('/api/packaging-cost/product-overview/export')
    expect(downloads[0].params).toMatchObject({ trend: 'down' })
    expect(downloads[0].params).not.toHaveProperty('page')
    expect(downloads[0].params).not.toHaveProperty('page_size')
  })

  it('sends the advanced filter to the server, counts it on the badge and exports with it', async () => {
    const user = userEvent.setup()
    build()
    await user.click(await screen.findByRole('button', { name: 'Lọc nâng cao' }))
    await user.click(screen.getByRole('button', { name: 'Chai' }))
    await user.type(screen.getByLabelText('% chênh từ'), '5')
    await user.click(screen.getByRole('button', { name: 'Áp dụng' }))
    await waitFor(() => expect(lastParams()).toMatchObject({ part_roles: '1', pct_min: 5, page: 1 }))
    expect(screen.getByRole('button', { name: /Lọc nâng cao/ })).toHaveTextContent('2')
    await user.click(screen.getByRole('button', { name: /Xuất Excel/ }))
    await waitFor(() => expect(downloads).toHaveLength(1))
    expect(downloads[0].params).toMatchObject({ part_roles: '1', pct_min: 5 })
    expect(downloads[0].params).not.toHaveProperty('page')
  })

  it('clears the advanced filter with "Xóa lọc"', async () => {
    const user = userEvent.setup()
    build()
    await user.click(await screen.findByRole('button', { name: 'Lọc nâng cao' }))
    await user.click(screen.getByRole('button', { name: 'Chai' }))
    await user.click(screen.getByRole('button', { name: 'Áp dụng' }))
    await waitFor(() => expect(lastParams()).toMatchObject({ part_roles: '1' }))
    await user.click(await screen.findByRole('button', { name: /Xóa lọc/ }))
    await waitFor(() => expect(lastParams()?.part_roles).toBeUndefined())
  })

  it('hides the export button without packaging_cost.export', async () => {
    canExport = false
    build()
    await screen.findByText('Thuốc trừ sâu A 1 lít')
    expect(screen.queryByRole('button', { name: /Xuất Excel/ })).not.toBeInTheDocument()
  })

  it('tells "no match" from "no product has a bill of materials"', async () => {
    result = { items: [], total: 0, counts: { all: 0, up: 0, down: 0, flat: 0, missing: 0 } }
    build()
    expect(await screen.findByText('Chưa có sản phẩm nào có định mức bao bì.')).toBeInTheDocument()
    const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: 'Tăng (0)' }))
    expect(await screen.findByText('Không có sản phẩm nào khớp bộ lọc.')).toBeInTheDocument()
  })
})
