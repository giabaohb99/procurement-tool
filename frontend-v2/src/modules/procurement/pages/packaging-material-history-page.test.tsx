// bao-CR-801 — màn Lịch sử mua nguyên liệu (mở từ mã ở Bảng giá nguyên liệu): dùng lại khuôn Lịch sử mua hàng của VTBB nhưng
// dữ liệu đi hai đường RIÊNG của nguyên liệu (`material-history`, `material-code-options`, khóa `packaging_material_price`).
// Người chỉ giữ khóa nguyên liệu gọi `history` / `code-options` / `fg-options` của VTBB là 403, nên bài kiểm canh chặt: màn
// KHÔNG được gọi ba đường đó dưới bất kỳ thao tác hay URL gõ tay nào. Chặn ở tầng `@/core/api` (luật testing.md).
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'
import { appRoutes } from '@/shared/constants/app-routes'

import type {
  PackagingCodeOption,
  PackagingHistoryResult,
  PackagingHistoryRow,
  PackagingHistoryStats,
} from '../types/packaging-cost-types'
import { PackagingMaterialHistoryPage } from './packaging-material-history-page'

const LIST_URL = '/api/packaging-cost/material-history'
const OPTIONS_URL = '/api/packaging-cost/material-code-options'
const EXPORT_URL = '/api/packaging-cost/material-history/export'
const PAGE_PATH = '/procurement/packaging-cost/material-history'

const calls: { url: string; params?: Record<string, unknown> }[] = []
const downloads: { url: string; name: string; params?: Record<string, unknown> }[] = []
let granted: string[] = []
let result: PackagingHistoryResult
let options: PackagingCodeOption[] = []

const stats = (over: Partial<PackagingHistoryStats> = {}): PackagingHistoryStats => ({
  purchase_count: 2,
  priced_count: 2,
  qty_total: 1500,
  weighted_avg: 1230000,
  min: 1200000,
  max: 1250000,
  supplier_count: 1,
  first_date: '2026-08-02',
  last_date: '2026-10-12',
  amount_total: 1_845_000_000,
  code_count: 2,
  product_count: 0,
  unit: 'Kg',
  first_price: 1200000,
  last_price: 1250000,
  ...over,
})

const row = (over: Partial<PackagingHistoryRow> = {}): PackagingHistoryRow => ({
  id: 11,
  date: '2026-10-12',
  code: 'NL0001',
  name: 'Hoạt chất Abamectin 95%',
  group: 'Nguyên liệu',
  supplier_code: 'HC01',
  supplier: 'Công ty Hóa chất A',
  warehouse: 'Kho nguyên liệu',
  qty: 1000,
  unit: 'Kg',
  price: 1250000,
  vat: 8,
  amount: 1_250_000_000,
  source_type: 2,
  line_stage: 2,
  is_open: false,
  doc_id: 55,
  po_code: 'PO-0055',
  prev_price: 1200000,
  diff: 50000,
  pct: 0.0417,
  seq: 1,
  fg_code: '',
  fg_name: '',
  role: null,
  ...over,
})

const option = (code: string): PackagingCodeOption => ({
  code,
  name: `Tên ${code}`,
  group: 'Nguyên liệu',
  usage: 0,
  new: 1000,
  suppliers: 'Công ty Hóa chất A',
})

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    apiGet: async (url: string, config?: { params?: Record<string, unknown> }) => {
      calls.push({ url, params: config?.params })
      if (url === LIST_URL) return result
      if (url === OPTIONS_URL) return { items: options }
      //  Mọi đường khác (nhất là ba đường của VTBB) coi như bị cấm — đúng cái người chỉ giữ khóa nguyên liệu gặp.
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

function Where() {
  const location = useLocation()
  return <p data-testid="where">{location.pathname + location.search}</p>
}

function build(search = '') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`${PAGE_PATH}${search}`]}>
        <PackagingMaterialHistoryPage />
        <Where />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const listCalls = () => calls.filter((call) => call.url === LIST_URL)
const lastListParams = () => listCalls().at(-1)?.params
const calledUrls = () => new Set(calls.map((call) => call.url))
const picker = () => screen.getByRole('combobox', { name: 'Chọn mã nguyên liệu' })

beforeEach(() => {
  calls.length = 0
  downloads.length = 0
  localStorage.clear()
  granted = ['packaging_material_price.read', 'packaging_material_price.export']
  result = {
    items: [
      row(),
      row({ id: 12, code: 'NL0002', name: 'Dung môi Xylene', date: '2026-08-02', price: 31000, doc_id: 0, po_code: '' }),
    ],
    total: 2,
    stats: stats(),
    series: null,
    series_by_code: null,
    suppliers: [{ code: 'HC01', name: 'Công ty Hóa chất A' }],
  }
  options = [option('NL0001'), option('NL0002'), option('NL0003')]
})

describe('PackagingMaterialHistoryPage', () => {
  it('loads the history of the code in the URL from material-history and never touches the VTBB endpoints', async () => {
    const user = userEvent.setup()
    build('?codes=NL0001')
    expect(await screen.findByText('Hoạt chất Abamectin 95%')).toBeInTheDocument()
    expect(listCalls()[0].params).toMatchObject({
      codes: ['NL0001'],
      sort_by: 'date',
      sort_dir: 'desc',
      page: 1,
      page_size: 50,
    })
    //  Đường nguyên liệu không có hai khóa này — không được gửi kèm, kể cả với giá trị rỗng.
    for (const key of ['mode', 'fg_codes']) expect(listCalls()[0].params).not.toHaveProperty(key)

    //  Đi qua mọi thao tác gọi máy chủ: xếp cột, chọn thêm mã, xuất.
    await waitFor(() => expect(picker()).toBeEnabled())
    await user.click(screen.getByText('Đơn giá'))
    await user.click(picker())
    await user.click(await screen.findByRole('option', { name: /NL0003/ }))
    await user.keyboard('{Escape}')
    await user.click(screen.getByRole('button', { name: /Xuất Excel/ }))
    await waitFor(() => expect(downloads).toHaveLength(1))

    expect(calledUrls()).toEqual(new Set([LIST_URL, OPTIONS_URL]))
    expect(calls.find((call) => call.url === OPTIONS_URL)?.params).toBeUndefined()
    expect(downloads[0].url).toBe(EXPORT_URL)
  })

  it('asks for every material when no code is picked', async () => {
    build()
    await screen.findByText('Hoạt chất Abamectin 95%')
    expect(listCalls()[0].params?.codes).toBeUndefined()
    for (const key of ['mode', 'fg_codes']) expect(listCalls()[0].params).not.toHaveProperty(key)
    expect(calledUrls()).toEqual(new Set([LIST_URL, OPTIONS_URL]))
  })

  it('ignores a crafted ?mode=product&fg= — it stays on codes and never loads the product list of VTBB', async () => {
    build('?mode=product&fg=HH0001,HH0002&codes=NL0002')
    await screen.findByText('Hoạt chất Abamectin 95%')
    await waitFor(() => expect(picker()).toBeEnabled())
    expect(listCalls()[0].params).toMatchObject({ codes: ['NL0002'] })
    for (const key of ['mode', 'fg_codes']) expect(listCalls()[0].params).not.toHaveProperty(key)
    expect(calledUrls()).toEqual(new Set([LIST_URL, OPTIONS_URL]))
    for (const header of ['Mã SP', 'Tên sản phẩm', 'Thành phần']) {
      expect(screen.queryByText(header)).not.toBeInTheDocument()
    }
    expect(screen.queryByRole('combobox', { name: 'Chọn mã sản phẩm' })).not.toBeInTheDocument()
  })

  it('has no product-mode tab, no Misa import and no print button — even for someone holding every VTBB right', async () => {
    granted.push(
      'packaging_history.read',
      'packaging_history.write',
      'packaging_history.export',
      'import.create',
      'import.read',
    )
    build('?codes=NL0001')
    await screen.findByText('Hoạt chất Abamectin 95%')
    expect(screen.queryByRole('radiogroup', { name: 'Chế độ chọn' })).not.toBeInTheDocument()
    expect(screen.queryByText('Theo mã sản phẩm')).not.toBeInTheDocument()
    expect(screen.queryByText('Theo mã VTBB')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Nạp sổ Misa/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'In' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'In' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Xuất Excel/ })).toBeInTheDocument()
  })

  it('shows Xuất Excel only with packaging_material_price.export — the VTBB export right does not count', async () => {
    granted = ['packaging_material_price.read', 'packaging_history.export', 'packaging_history.read']
    const first = build('?codes=NL0001')
    await screen.findByText('Hoạt chất Abamectin 95%')
    expect(screen.queryByRole('button', { name: /Xuất Excel/ })).not.toBeInTheDocument()
    first.unmount()

    granted = ['packaging_material_price.read', 'packaging_material_price.export']
    build('?codes=NL0001')
    await screen.findByText('Hoạt chất Abamectin 95%')
    expect(screen.getByRole('button', { name: /Xuất Excel/ })).toBeInTheDocument()
  })

  it('exports the codes and order on screen to the material export endpoint, without page, mode or fg_codes', async () => {
    const user = userEvent.setup()
    build('?codes=NL0001,NL0002')
    await screen.findByText('Hoạt chất Abamectin 95%')
    await user.click(screen.getByText('Giá trị mua'))
    await waitFor(() => expect(lastListParams()).toMatchObject({ sort_by: 'amount', sort_dir: 'desc' }))
    await user.click(screen.getByRole('button', { name: /Xuất Excel/ }))
    await waitFor(() => expect(downloads).toHaveLength(1))
    expect(downloads[0]).toMatchObject({ url: EXPORT_URL, name: 'lich-su-mua-nguyen-lieu.xlsx' })
    expect(downloads[0].params).toMatchObject({
      codes: ['NL0001', 'NL0002'],
      sort_by: 'amount',
      sort_dir: 'desc',
    })
    for (const key of ['page', 'page_size', 'mode', 'fg_codes']) {
      expect(downloads[0].params).not.toHaveProperty(key)
    }
  })

  it('labels the columns for raw materials, keeps the code as plain text and the purchase order link in Nguồn', async () => {
    //  Kể cả người đọc được Lịch sử mua hàng của VTBB: màn đó không có mã nguyên liệu nên mã ở đây không dẫn sang đó.
    granted.push('packaging_history.read', 'purchase_order.read')
    build()
    const line = (await screen.findByText('Hoạt chất Abamectin 95%')).closest('tr') as HTMLTableRowElement
    expect(screen.getByText('Mã nguyên liệu')).toBeInTheDocument()
    expect(screen.getByText('Tên nguyên liệu')).toBeInTheDocument()
    for (const header of ['Mã VTBB', 'Tên vật tư']) {
      expect(screen.queryByText(header)).not.toBeInTheDocument()
    }
    expect(within(line).getByText('NL0001')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /^NL000/ })).not.toBeInTheDocument()
    expect(within(line).getByRole('link', { name: 'PO-0055' })).toHaveAttribute(
      'href',
      appRoutes.procurement.purchaseOrderDetail(55),
    )
  })

  it('shows the purchase order number as plain text without purchase_order.read', async () => {
    build()
    const line = (await screen.findByText('Hoạt chất Abamectin 95%')).closest('tr') as HTMLTableRowElement
    expect(within(line).getByText('PO-0055')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'PO-0055' })).not.toBeInTheDocument()
  })

  it('keeps the picked codes on the URL and asks the server again from page 1', async () => {
    const user = userEvent.setup()
    result = { ...result, total: 120 }
    build('?codes=NL0001')
    await screen.findByText('Hoạt chất Abamectin 95%')
    await user.click(screen.getByRole('button', { name: 'Trang sau' }))
    await waitFor(() => expect(lastListParams()).toMatchObject({ page: 2 }))

    await waitFor(() => expect(picker()).toBeEnabled())
    await user.click(picker())
    await user.click(await screen.findByRole('option', { name: /NL0003/ }))
    await waitFor(() =>
      expect(lastListParams()).toMatchObject({ codes: ['NL0001', 'NL0003'], page: 1 }),
    )
    expect(screen.getByTestId('where')).toHaveTextContent(`${PAGE_PATH}?codes=NL0001%2CNL0003`)
    for (const key of ['mode', 'fg_codes']) expect(lastListParams()).not.toHaveProperty(key)
  })

  it('switches to the single-code cards and drops the name column when the server returns a price series', async () => {
    result = {
      ...result,
      items: [row()],
      total: 1,
      stats: stats({ purchase_count: 1, code_count: 1 }),
      series: [],
    }
    build('?codes=NL0001')
    expect(await screen.findByText('Tổng số lượng mua')).toBeInTheDocument()
    expect(screen.getByText('Giá thấp nhất – cao nhất')).toBeInTheDocument()
    expect(screen.getByText('Mã nguyên liệu')).toBeInTheDocument()
    expect(screen.queryByText('Tên nguyên liệu')).not.toBeInTheDocument()
  })

  it('says there is no purchase for a code without history, still calling the material endpoints only', async () => {
    result = { ...result, items: [], total: 0, stats: stats({ purchase_count: 0, code_count: 0 }) }
    build('?codes=NL0009')
    expect(await screen.findByText('Chưa có lần mua nào cho lựa chọn này.')).toBeInTheDocument()
    //  Mã lạ trên URL (không có trong danh sách ô chọn) vẫn chỉ đi đường nguyên liệu.
    expect(listCalls()[0].params).toMatchObject({ codes: ['NL0009'] })
    expect(calledUrls()).toEqual(new Set([LIST_URL, OPTIONS_URL]))
  })
})
