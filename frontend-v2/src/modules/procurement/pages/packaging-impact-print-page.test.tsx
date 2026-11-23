// duoc-CR-784 — bản in Tác động giá bao bì: gửi đúng thân POST /impact (mã + giá giả định + tìm / xếp) từng trang 500 sản
// phẩm tới khi đủ, cắt ở 5.000 và báo rõ, hai bảng + dòng tóm tắt, tự mở hộp thoại in một lần, KHÔNG mở khi lỗi hoặc
// chưa chọn mã. Chặn ở tầng `@/core/api` (luật testing.md).
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'

import type {
  PackagingImpactProduct,
  PackagingImpactResult,
  PackagingSelectedCode,
} from '../types/packaging-cost-types'
import { PackagingImpactPrintPage } from './packaging-impact-print-page'

const calls: { url: string; body: Record<string, unknown> }[] = []
let total = 0
let failWith: Error | null = null

const selected: PackagingSelectedCode[] = [
  {
    code: 'CPT0105', name: 'Chai 1L', group: 'Chai', unit: 'Cái', old: 1000, new: 1100, assumed: 1250,
    applied: 1250, diff: 250, pct: 0.25, usage: 2, min: 900, max: 1300, floor: null, ceiling: null,
  },
  {
    code: 'NAP0085', name: 'Nắp 28mm', group: 'Nắp', unit: 'Cái', old: 300, new: 300, assumed: null,
    applied: 300, diff: 0, pct: 0, usage: 1, min: 280, max: 320, floor: null, ceiling: null,
  },
]

const product = (n: number): PackagingImpactProduct => ({
  hh_code: `HH${String(n).padStart(5, '0')}`,
  hh_name: `Sản phẩm ${n}`,
  carton_qty: 12,
  parts: [
    { role: 1, code: 'CPT0105', old: 1000, new: 1100, applied: 1250, selected: true },
    { role: 2, code: 'NAP0085', old: 300, new: 300, applied: 300, selected: false },
  ],
  cost_old_bottle: 1300,
  cost_new_bottle: 1400,
  cost_applied_bottle: 1550,
  diff_bottle: 250,
  pct: 0.19,
  cost_old_carton: 15600,
  cost_applied_carton: 18600,
  diff_carton: 3000,
  trend: 1,
  warnings: [],
})

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    apiPost: async (url: string, body: Record<string, unknown>) => {
      calls.push({ url, body })
      if (failWith) throw failWith
      const page = Number(body.page)
      const size = Number(body.page_size)
      const start = (page - 1) * size
      const count = Math.max(0, Math.min(size, total - start))
      const result: PackagingImpactResult = {
        selected,
        kpis: {
          selected_count: 2, selected_by_group: { Chai: 1, Nắp: 1 }, assumed_count: 1,
          affected_products: total, increased: total, decreased: 0,
          max_increase_carton: 3000, max_increase_bottle: 250,
          max_increase_product: { hh_code: 'HH0003', hh_name: 'Sản phẩm ba', diff_bottle: 250, diff_carton: 3000, carton_qty: 12 },
        },
        products: Array.from({ length: count }, (_, i) => product(start + i + 1)),
        products_total: total,
      }
      return result
    },
  }
})

function build(query: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/print/packaging-impact?${query}`]}>
        <PackagingImpactPrintPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const printSpy = vi.fn()
const productRows = () => document.querySelectorAll('.panel.gap tbody tr')

beforeEach(() => {
  calls.length = 0
  total = 0
  failWith = null
  printSpy.mockReset()
  vi.stubGlobal('print', printSpy)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('PackagingImpactPrintPage', () => {
  it('prints the header, filter line, summary, both tables and opens the print dialog once', async () => {
    total = 3
    build('codes=CPT0105,NAP0085&assumed=CPT0105:1250&q=b07&sort_by=diff_carton&sort_dir=desc')
    expect(await screen.findByRole('heading', { name: 'BÁO CÁO GIÁ NGUYÊN VẬT LIỆU SẢN XUẤT' })).toBeInTheDocument()
    expect(screen.getByText(/Báo cáo giá › Tác động giá bao bì/)).toBeInTheDocument()
    expect(await screen.findAllByText(/^(CPT0105|NAP0085)$/, { selector: '.mchip' })).toHaveLength(2)
    //  Dòng thông tin chỉ còn các điều kiện đang bật; ba thẻ số liệu đã bỏ khỏi bản in theo người chủ (23/11/2026).
    expect(document.querySelector('.info')).toHaveTextContent('Giá giả định: CPT0105 = 1.250 · Tìm sản phẩm: "b07"')
    expect(document.querySelectorAll('.kpi')).toHaveLength(0)
    expect(screen.getByRole('columnheader', { name: 'Giá giả định' })).toBeInTheDocument()
    expect(screen.queryByRole('columnheader', { name: /Sàn/ })).not.toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Nhãn thùng (giá /thùng)' })).toBeInTheDocument()
    expect(productRows()).toHaveLength(3)
    expect(screen.getByText(/FOR A BETTER LIFE/)).toBeInTheDocument()
    expect(calls[0].url).toBe('/api/packaging-cost/impact')
    expect(calls[0].body).toMatchObject({
      codes: ['CPT0105', 'NAP0085'],
      assumed_prices: { CPT0105: 1250 },
      q: 'b07',
      sort_by: 'diff_carton',
      sort_dir: 'desc',
      page: 1,
      page_size: 500,
    })
    await waitFor(() => expect(printSpy).toHaveBeenCalledTimes(1), { timeout: 3000 })
  })

  it('pages through 500 products at a time until all are loaded', async () => {
    total = 1203
    build('codes=CPT0105')
    await waitFor(() => expect(productRows()).toHaveLength(1203), { timeout: 5000 })
    expect(calls.map((call) => call.body.page)).toEqual([1, 2, 3])
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('stops at 5,000 products and says so', async () => {
    total = 5300
    build('codes=CPT0105')
    expect(await screen.findByRole('status')).toHaveTextContent(/5\.300 sản phẩm.*5\.000 dòng đầu/)
    expect(productRows()).toHaveLength(5000)
    expect(calls).toHaveLength(10)
  }, 20000)

  it('says there is nothing to print when no product uses the selected codes', async () => {
    total = 0
    build('codes=CPT0105&q=zzz')
    expect(await screen.findByText('Không có sản phẩm khớp từ khóa / bộ lọc.')).toBeInTheDocument()
  })

  it('forwards the advanced filters and component sort key to every page request and prints them as conditions', async () => {
    total = 0
    build('codes=CPT0105&trend=up&part_roles=1,5&carton_qty_min=12&warnings_only=1&sort_by=part_bottle&sort_dir=desc')
    expect(await screen.findByText('Không có sản phẩm khớp từ khóa / bộ lọc.')).toBeInTheDocument()
    expect(calls[0].body).toMatchObject({
      trend: 'up',
      part_roles: [1, 5],
      carton_qty_min: 12,
      warnings_only: true,
      sort_by: 'part_bottle',
      sort_dir: 'desc',
    })
    expect(screen.getByText(/Xu hướng: Tăng/)).toBeInTheDocument()
    expect(screen.getByText(/Mã đã chọn ở vai trò: Chai, Thùng/)).toBeInTheDocument()
  })

  it('does not call the server or print when the link has no codes', async () => {
    build('assumed=A:5')
    expect(await screen.findByRole('alert')).toHaveTextContent(/Chưa chọn mã nào để in/)
    await new Promise((resolve) => setTimeout(resolve, 800))
    expect(calls).toHaveLength(0)
    expect(printSpy).not.toHaveBeenCalled()
  })

  it('shows the error and never opens the print dialog when the API fails', async () => {
    failWith = new Error('Máy chủ từ chối')
    build('codes=CPT0105')
    expect(await screen.findByRole('alert')).toHaveTextContent(/Không tải được số liệu tác động giá/)
    await new Promise((resolve) => setTimeout(resolve, 800))
    expect(printSpy).not.toHaveBeenCalled()
  })
})
