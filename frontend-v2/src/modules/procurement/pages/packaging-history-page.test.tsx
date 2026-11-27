// bao-CR-801 — bài CANH của màn Lịch sử mua hàng (VTBB) sau khi khuôn màn được dùng chung cho Lịch sử mua nguyên liệu: màn
// VTBB phải giữ nguyên hành vi — vẫn đi `history` + `code-options?scope=all` (+ `fg-options` ở chế độ sản phẩm), vẫn có hai
// nút chế độ, nút In, nút Nạp sổ Misa, Xuất Excel theo `packaging_history.export`, mã là đường bấm — và KHÔNG gọi đường nào
// của nguyên liệu (người chỉ giữ khóa Lịch sử mua hàng gọi `material-*` là 403).
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'
import { appRoutes } from '@/shared/constants/app-routes'

import type {
  PackagingCodeOption,
  PackagingHistoryResult,
  PackagingHistoryRow,
  PackagingHistoryStats,
} from '../types/packaging-cost-types'
import { PackagingHistoryPage } from './packaging-history-page'

const LIST_URL = '/api/packaging-cost/history'
const OPTIONS_URL = '/api/packaging-cost/code-options'
const FG_OPTIONS_URL = '/api/packaging-cost/fg-options'
const EXPORT_URL = '/api/packaging-cost/history/export'

const calls: { url: string; params?: Record<string, unknown> }[] = []
const downloads: { url: string; name: string; params?: Record<string, unknown> }[] = []
let granted: string[] = []
let result: PackagingHistoryResult

const stats: PackagingHistoryStats = {
  purchase_count: 1,
  priced_count: 1,
  qty_total: 2000,
  weighted_avg: 900,
  min: 900,
  max: 900,
  supplier_count: 1,
  first_date: '2026-09-11',
  last_date: '2026-09-11',
  amount_total: 1_800_000,
  code_count: 1,
  product_count: 0,
  unit: 'Cái',
  first_price: 900,
  last_price: 900,
}

const row = (over: Partial<PackagingHistoryRow> = {}): PackagingHistoryRow => ({
  id: 7,
  date: '2026-09-11',
  code: 'NAP0029',
  name: 'Nắp HD cổ 50 trắng',
  group: 'Nắp',
  supplier_code: 'N1',
  supplier: 'Công ty Nắp Việt',
  warehouse: 'Kho Dego',
  qty: 2000,
  unit: 'Cái',
  price: 900,
  vat: 8,
  amount: 1_800_000,
  source_type: 2,
  line_stage: 2,
  is_open: false,
  doc_id: 0,
  po_code: '',
  prev_price: null,
  diff: null,
  pct: null,
  seq: 1,
  fg_code: '',
  fg_name: '',
  role: null,
  ...over,
})

const codeOptions: PackagingCodeOption[] = [
  { code: 'NAP0029', name: 'Nắp HD cổ 50 trắng', group: 'Nắp', usage: 3, new: 900 },
]

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    apiGet: async (url: string, config?: { params?: Record<string, unknown> }) => {
      calls.push({ url, params: config?.params })
      if (url === LIST_URL) return result
      if (url === OPTIONS_URL) return { items: codeOptions }
      if (url === FG_OPTIONS_URL) return { items: [{ code: 'HH0001', name: 'Thuốc trừ sâu A 100ml' }] }
      //  Mọi đường khác (nhất là hai đường của nguyên liệu) coi như bị cấm.
      throw new Error(`403 ${url}`)
    },
    downloadFile: async (url: string, name: string, params?: Record<string, unknown>) => {
      downloads.push({ url, name, params })
    },
  }
})

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string, action: string) => granted.includes(`${entity}.${action}`),
    canAccess: () => true,
  }),
}))

function build(search = '') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`${appRoutes.procurement.packagingHistory}${search}`]}>
        <PackagingHistoryPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const listCalls = () => calls.filter((call) => call.url === LIST_URL)
const calledUrls = () => new Set(calls.map((call) => call.url))

beforeEach(() => {
  calls.length = 0
  downloads.length = 0
  localStorage.clear()
  granted = ['packaging_history.read', 'packaging_history.export']
  result = {
    items: [row()],
    total: 1,
    stats,
    series: null,
    series_by_code: null,
    suppliers: [{ code: 'N1', name: 'Công ty Nắp Việt' }],
  }
})

describe('PackagingHistoryPage (VTBB) — unchanged by the shared material history screen', () => {
  it('loads the code in the URL through history + code-options?scope=all and never asks a material endpoint', async () => {
    const user = userEvent.setup()
    build('?codes=NAP0029')
    expect(await screen.findByText('Nắp HD cổ 50 trắng')).toBeInTheDocument()
    expect(listCalls()[0].params).toMatchObject({
      mode: 'code',
      codes: ['NAP0029'],
      sort_by: 'date',
      sort_dir: 'desc',
      page: 1,
      page_size: 50,
    })
    await user.click(screen.getByText('Đơn giá'))
    await user.click(screen.getByRole('button', { name: /Xuất Excel/ }))
    await waitFor(() => expect(downloads).toHaveLength(1))

    expect(calledUrls()).toEqual(new Set([LIST_URL, OPTIONS_URL]))
    expect(calls.find((call) => call.url === OPTIONS_URL)?.params).toEqual({ scope: 'all' })
    expect(downloads[0]).toMatchObject({ url: EXPORT_URL, name: 'lich-su-mua-hang.xlsx' })
    expect(downloads[0].params).toMatchObject({ mode: 'code', codes: ['NAP0029'] })
    for (const key of ['page', 'page_size']) expect(downloads[0].params).not.toHaveProperty(key)
  })

  it('keeps the mode tabs, the print link, the Misa import and the VTBB column labels with a code link', async () => {
    granted.push('packaging_history.write', 'import.create', 'import.read')
    build('?codes=NAP0029')
    const line = (await screen.findByText('Nắp HD cổ 50 trắng')).closest('tr') as HTMLTableRowElement
    const modes = screen.getByRole('radiogroup', { name: 'Chế độ chọn' })
    expect(within(modes).getByText('Theo mã VTBB')).toBeInTheDocument()
    expect(within(modes).getByText('Theo mã sản phẩm')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'In' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Nạp sổ Misa/ })).toBeInTheDocument()
    expect(screen.getByText('Mã VTBB')).toBeInTheDocument()
    expect(screen.getByText('Tên vật tư')).toBeInTheDocument()
    expect(screen.queryByText('Mã nguyên liệu')).not.toBeInTheDocument()
    expect(within(line).getByRole('link', { name: 'NAP0029' })).toHaveAttribute(
      'href',
      `${appRoutes.procurement.packagingHistory}?codes=NAP0029`,
    )
  })

  it('switches to product mode from a ?fg= link: loads the product list and sends fg_codes', async () => {
    result = {
      ...result,
      items: [row({ fg_code: 'HH0001', fg_name: 'Thuốc trừ sâu A 100ml', role: 2 })],
    }
    build('?fg=HH0001')
    expect(await screen.findByText('Thuốc trừ sâu A 100ml')).toBeInTheDocument()
    expect(listCalls()[0].params).toMatchObject({ mode: 'product', fg_codes: ['HH0001'] })
    expect(listCalls()[0].params?.codes).toBeUndefined()
    await waitFor(() => expect(calledUrls()).toContain(FG_OPTIONS_URL))
    expect(screen.getByText('Mã SP')).toBeInTheDocument()
    expect(calledUrls()).toEqual(new Set([LIST_URL, OPTIONS_URL, FG_OPTIONS_URL]))
  })

  it('gates Xuất Excel by packaging_history.export — the material export right does not count', async () => {
    granted = ['packaging_history.read', 'packaging_material_price.export', 'packaging_material_price.read']
    build('?codes=NAP0029')
    await screen.findByText('Nắp HD cổ 50 trắng')
    expect(screen.queryByRole('button', { name: /Xuất Excel/ })).not.toBeInTheDocument()
    expect(calledUrls()).toEqual(new Set([LIST_URL, OPTIONS_URL]))
  })
})
