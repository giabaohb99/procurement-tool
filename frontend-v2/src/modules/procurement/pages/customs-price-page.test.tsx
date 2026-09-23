// bao-CR-470 — màn Tra cứu giá hải quan: cổng "chưa lọc thì không vẽ biểu đồ", câu bảng
// rỗng phân biệt «chưa có dữ liệu» với «bộ lọc loại hết», và nút Nạp dữ liệu gác theo quyền.
// Chặn ở tầng `@/core/api` (luật testing.md) để bắt được đúng đường API màn gọi đi.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'

import { CustomsPricePage } from './customs-price-page'

const calls: { url: string; params?: Record<string, unknown> }[] = []
let coverageTotal = 120
let lineItems: unknown[] = []

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    apiGet: async (url: string, config?: { params?: Record<string, unknown> }) => {
      calls.push({ url, params: config?.params })
      if (url.endsWith('/coverage')) {
        return {
          total: coverageTotal,
          date_from: '2026-01-02',
          date_to: '2026-09-17',
          last_import_at: null,
          years: [{ year: 2026, months: [1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0] }],
        }
      }
      if (url.endsWith('/options')) {
        return {
          hs_codes: [],
          origins: [],
          units: [],
          ingredients: [],
          formulations: [],
          ingredient_coverage: { total: 0, tagged: 0, ratio: null },
        }
      }
      if (url.endsWith('/lines')) return { total: lineItems.length, items: lineItems }
      if (url.endsWith('/alerts')) return []
      if (url.endsWith('/stats')) {
        return {
          period: 'month',
          price_mode: 'adjusted',
          unit: 'KGM',
          units: [{ unit: 'KGM', count: 3 }],
          series: [],
          kpi: { count: 3, qty: 10, min: 2, max: 4, wavg: 3, outliers: 1 },
          best_period: null,
          min_lines_for_best: 5,
          coverage: { lines: 3, months: 1, years: 1, date_from: null, date_to: null, empty_periods: [] },
        }
      }
      throw new Error(`Không mock đường ${url}`)
    },
  }
})

let canWrite = true

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string, action: string) => {
      if (entity === 'customs_price' && action === 'write') return canWrite
      return true
    },
    canAccess: () => true,
  }),
}))

function build(url: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <CustomsPricePage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  calls.length = 0
  coverageTotal = 120
  lineItems = []
  canWrite = true
})

describe('CustomsPricePage', () => {
  it('blocks the chart tab with the need-filter message and never calls /stats without a keyword or HS code', async () => {
    build('/procurement/customs-prices?tab=chart&origin=CN')
    expect(
      await screen.findByText('Nhập tên hàng / hoạt chất hoặc chọn mã HS để xem biểu đồ.'),
    ).toBeInTheDocument()
    await waitFor(() => expect(calls.some((call) => call.url.endsWith('/coverage'))).toBe(true))
    expect(calls.some((call) => call.url.endsWith('/stats'))).toBe(false)
  })

  it('blocks the importers tab the same way', async () => {
    build('/procurement/customs-prices?tab=importers')
    expect(
      await screen.findByText('Nhập tên hàng / hoạt chất hoặc chọn mã HS để xem biểu đồ.'),
    ).toBeInTheDocument()
  })

  it('loads the chart with the HS code filter when one is set', async () => {
    build('/procurement/customs-prices?tab=chart&hs_code=3808')
    await waitFor(() => expect(calls.some((call) => call.url.endsWith('/stats'))).toBe(true))
    const stats = calls.find((call) => call.url.endsWith('/stats'))
    expect(stats?.params).toMatchObject({ hs_code: '3808', period: 'month', price_mode: 'adjusted' })
    expect(await screen.findByText(/1 dòng giá bất thường/)).toBeInTheDocument()
  })

  it('says there is no customs data yet when nothing has ever been imported', async () => {
    coverageTotal = 0
    build('/procurement/customs-prices')
    expect(
      await screen.findByText('Chưa có dữ liệu hải quan. Bấm «Nạp dữ liệu» để tải tệp GTT02.'),
    ).toBeInTheDocument()
  })

  it('says the filter excluded everything when data exists but no line matches', async () => {
    build('/procurement/customs-prices?q=khongco')
    expect(
      await screen.findByText(
        'Không có dòng hàng nào khớp bộ lọc — thử bỏ bớt điều kiện hoặc đổi từ khóa.',
      ),
    ).toBeInTheDocument()
    const lines = calls.find((call) => call.url.endsWith('/lines'))
    expect(lines?.params).toMatchObject({ q: 'khongco', page: 1 })
  })

  it('hides the import button without customs_price.write', async () => {
    canWrite = false
    build('/procurement/customs-prices')
    expect(await screen.findByRole('button', { name: /Lịch sử nạp/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Nạp dữ liệu/ })).not.toBeInTheDocument()
  })
})
