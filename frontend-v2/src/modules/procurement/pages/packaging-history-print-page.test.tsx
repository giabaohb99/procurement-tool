// duoc-CR-784 — bản in Lịch sử mua hàng: nạp ĐỦ mọi dòng bằng cách lật trang 500 dòng, cắt ở 5.000 và báo rõ, KPI + biểu
// đồ chỉ khi đúng một mã, tự mở hộp thoại in một lần khi có dữ liệu, KHÔNG mở khi lỗi. Chặn ở tầng `@/core/api` (luật testing.md).
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'

import type {
  PackagingHistoryResult,
  PackagingHistoryRow,
} from '../types/packaging-cost-types'
import { PackagingHistoryPrintPage } from './packaging-history-print-page'

const calls: { url: string; params: Record<string, unknown> }[] = []
let total = 0
let single = false
let failWith: Error | null = null

const row = (id: number, over: Partial<PackagingHistoryRow> = {}): PackagingHistoryRow => ({
  id,
  date: '2026-03-05',
  code: 'CET0028',
  name: 'Chai nhựa 1L',
  group: 'Chai',
  supplier_code: 'NCC01',
  supplier: 'Nhựa Á Châu',
  warehouse: 'Kho DEGO Cần Thơ',
  qty: 1500,
  unit: 'Cái',
  price: 1200,
  vat: 0.08,
  amount: 1_800_000,
  source_type: 1,
  doc_id: 0,
  po_code: '',
  prev_price: 1000,
  diff: 200,
  pct: 0.2,
  seq: id,
  roles: [],
  ...over,
})

const stats = {
  purchase_count: 9,
  priced_count: 9,
  qty_total: 9000,
  weighted_avg: 1100.5,
  min: 1000,
  max: 1200,
  supplier_count: 2,
  first_date: '2026-01-01',
  last_date: '2026-05-01',
}

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    apiGet: async (url: string, config?: { params?: Record<string, unknown> }) => {
      const params = config?.params ?? {}
      calls.push({ url, params })
      if (failWith) throw failWith
      const page = Number(params.page)
      const size = Number(params.page_size)
      const start = (page - 1) * size
      const count = Math.max(0, Math.min(size, total - start))
      const items = Array.from({ length: count }, (_, i) =>
        row(start + i + 1, i === 0 && page === 1 ? { po_code: 'PO00012', doc_id: 12, source_type: 2 } : {}),
      )
      const result: PackagingHistoryResult = {
        items,
        total,
        stats,
        series: single ? [{ date: '2026-01-01', price: 1000, supplier_code: 'NCC01', supplier: 'A', qty: 10 },
          { date: '2026-03-05', price: 1200, supplier_code: 'NCC01', supplier: 'A', qty: 10 }] : null,
        suppliers: [{ code: 'NCC01', name: 'Nhựa Á Châu' }],
      }
      return result
    },
  }
})

function build(query: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/print/packaging-history?${query}`]}>
        <PackagingHistoryPrintPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const printSpy = vi.fn()

/** Đếm thẳng DOM: truy vấn theo vai trò trên 5.000 dòng mất cả chục giây trong jsdom. */
const bodyRows = () => document.querySelectorAll('tbody tr')

beforeEach(() => {
  calls.length = 0
  total = 0
  single = false
  failWith = null
  printSpy.mockReset()
  vi.stubGlobal('print', printSpy)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('PackagingHistoryPrintPage', () => {
  it('shows the report header, filter line, KPI boxes and every row, then opens the print dialog once', async () => {
    total = 9
    single = true
    build('mode=code&codes=CET0028&supplier=NCC01&date_from=2026-01-01')
    expect(await screen.findByRole('heading', { name: 'BÁO CÁO GIÁ NGUYÊN VẬT LIỆU SẢN XUẤT' })).toBeInTheDocument()
        // Ô lọc dựng như bản mẫu: chip chế độ + chip mã + dòng thông tin (tên mã, NCC, khoảng ngày).
    expect(await screen.findByText('Mã VTBB', { selector: '.chip.on' })).toBeInTheDocument()
    expect(screen.getByText('CET0028', { selector: '.mchip' })).toBeInTheDocument()
    expect(document.querySelector('.info')).toHaveTextContent(
      'CET0028 — Chai nhựa 1L · Chai · ĐVT Cái · NCC: Nhựa Á Châu · Ngày mua: từ 01/01/2026',
    )
    // 1 dòng tiêu đề + 9 dòng dữ liệu; đúng một mã nên có đủ 7 thẻ và không có cột Tên vật tư.
    expect(bodyRows()).toHaveLength(9)
    expect(screen.queryByRole('columnheader', { name: 'Tên vật tư' })).not.toBeInTheDocument()
    expect(screen.getByText('Giá BQ gia quyền')).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'Diễn biến đơn giá' })).toBeInTheDocument()
    expect(screen.getByText('ĐMH đang mở')).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Kho' })).toBeInTheDocument()
    expect(screen.getAllByText('Kho DEGO Cần Thơ').length).toBeGreaterThan(0)
    expect(screen.getByText('PO00012')).toBeInTheDocument()
    expect(screen.getAllByText('+200 (+20,0%)').length).toBeGreaterThan(0)
    // Chân trang thương hiệu chỉ trên màn hình (CSS ẩn khi in), nhưng vẫn có trong trang.
    expect(screen.getByText(/FOR A BETTER LIFE/)).toBeInTheDocument()
    expect(screen.getByText(/Phòng Thu mua › Báo cáo giá › Lịch sử mua hàng/)).toBeInTheDocument()
    expect(calls).toHaveLength(1)
    expect(calls[0].params).toMatchObject({ mode: 'code', codes: ['CET0028'], page: 1, page_size: 500 })
    await waitFor(() => expect(printSpy).toHaveBeenCalledTimes(1), { timeout: 3000 })
  })

  it('pages through the server 500 rows at a time until every row is loaded', async () => {
    total = 1203
    build('mode=code')
    await screen.findByRole('table')
    await waitFor(() => expect(bodyRows()).toHaveLength(1203))
    expect(calls.map((call) => call.params.page)).toEqual([1, 2, 3])
    // Nhiều mã: không có thẻ giá, có cột tên, và có câu nhắc chọn đúng một mã.
    expect(screen.queryByText('Giá BQ gia quyền')).not.toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Tên vật tư' })).toBeInTheDocument()
    expect(screen.getByText(/Chọn đúng một mã để xem giá bình quân/)).toBeInTheDocument()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('stops at 5,000 rows and says so on the page', async () => {
    total = 6200
    build('mode=code')
    expect(await screen.findByRole('status')).toHaveTextContent(/6\.200 lần mua.*5\.000 dòng đầu/)
    expect(bodyRows()).toHaveLength(5000)
    expect(calls).toHaveLength(10)
  }, 20000)

  it('adds the role column in product mode and survives a hostile URL', async () => {
    total = 1
    build('mode=product&hh_codes=HH0417.1&sort_by=evil&date_from=never')
    const header = await screen.findByRole('columnheader', { name: 'Vai trò' })
    expect(within(header.closest('table') as HTMLElement).getAllByRole('row')).toHaveLength(2)
    expect(calls[0].params).toMatchObject({ mode: 'product', hh_codes: ['HH0417.1'] })
    expect(calls[0].params.sort_by).toBeUndefined()
    expect(calls[0].params.date_from).toBeUndefined()
  })

  it('shows a clear empty message when the filter matches nothing', async () => {
    total = 0
    build('mode=code&codes=KHONGCO')
    expect(await screen.findByText('Không có lần mua nào khớp bộ lọc.')).toBeInTheDocument()
  })

  it('shows the error and never opens the print dialog when the API fails', async () => {
    failWith = new Error('Máy chủ từ chối')
    build('mode=code&codes=CET0028')
    expect(await screen.findByRole('alert')).toHaveTextContent(/Không tải được lịch sử mua hàng/)
    await new Promise((resolve) => setTimeout(resolve, 800))
    expect(printSpy).not.toHaveBeenCalled()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })
})
