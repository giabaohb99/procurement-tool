// bao-CR-470 — màn Tra cứu giá hải quan: cổng "chưa lọc thì không vẽ biểu đồ", câu bảng
// rỗng phân biệt «chưa có dữ liệu» với «bộ lọc loại hết», và nút Nạp dữ liệu gác theo quyền.
// Chặn ở tầng `@/core/api` (luật testing.md) để bắt được đúng đường API màn gọi đi.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
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
let canManageConfig = true
let canReadRegulations = true

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string, action: string) => {
      if (entity === 'customs_price' && action === 'write') return canWrite
      if (entity === 'customs_price' && (action === 'create' || action === 'delete')) {
        return canManageConfig
      }
      if (entity === 'customs_regulation') return canReadRegulations
      return true
    },
    canAccess: () => true,
  }),
}))

/** Hiện đường + query hiện tại để khẳng định chỗ trang tự chuyển tới. */
function LocationProbe() {
  const { pathname, search } = useLocation()
  return <output aria-label="location">{`${pathname}${search}`}</output>
}

//  Khớp đúng hai route khai ở `routes.tsx`: đường gốc (Danh sách) + `/:section`.
function build(url: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <Routes>
          <Route path="/procurement/customs-prices" element={<CustomsPricePage />} />
          <Route path="/procurement/customs-prices/:section" element={<CustomsPricePage />} />
        </Routes>
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function currentLocation() {
  return screen.getByRole('status', { name: 'location' }).textContent
}

beforeEach(() => {
  calls.length = 0
  coverageTotal = 120
  lineItems = []
  canWrite = true
  canManageConfig = true
  canReadRegulations = true
})

describe('CustomsPricePage', () => {
  it('blocks the chart tab with the need-filter message and never calls /stats without a keyword or HS code', async () => {
    build('/procurement/customs-prices/chart?origin=CN')
    expect(
      await screen.findByText('Nhập tên hàng / hoạt chất hoặc chọn mã HS để xem biểu đồ.'),
    ).toBeInTheDocument()
    await waitFor(() => expect(calls.some((call) => call.url.endsWith('/coverage'))).toBe(true))
    expect(calls.some((call) => call.url.endsWith('/stats'))).toBe(false)
  })

  it('blocks the importers tab the same way', async () => {
    build('/procurement/customs-prices/importers')
    expect(
      await screen.findByText('Nhập tên hàng / hoạt chất hoặc chọn mã HS để xem biểu đồ.'),
    ).toBeInTheDocument()
  })

  it('loads the chart with the HS code filter when one is set', async () => {
    build('/procurement/customs-prices/chart?hs_code=3808')
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

  //  Link cũ (thẻ chưa thành submenu) còn nằm trong thông báo, lịch sử trình duyệt, tin nhắn —
  //  phải rơi đúng mục và GIỮ bộ lọc, không được rơi về Danh sách trống trơn.
  it('redirects a legacy ?tab= link to the section path and keeps the filters', async () => {
    build('/procurement/customs-prices?tab=chart&hs_code=3808')
    await waitFor(() =>
      expect(currentLocation()).toBe('/procurement/customs-prices/chart?hs_code=3808'),
    )
    await waitFor(() => expect(calls.some((call) => call.url.endsWith('/stats'))).toBe(true))
  })

  it('sends /list back to the base path so the «Danh sách» menu item lights up', async () => {
    build('/procurement/customs-prices/list?origin=CN')
    await waitFor(() => expect(currentLocation()).toBe('/procurement/customs-prices?origin=CN'))
  })

  //  «Pháp lý & thuế» chia đôi 29/09/2026: link cũ `?tab=legal` phải rơi vào mục Pháp lý.
  it('lands an old ?tab=legal link on the Pháp lý section', async () => {
    build('/procurement/customs-prices?tab=legal')
    await waitFor(() => expect(currentLocation()).toBe('/procurement/customs-prices/legal'))
  })

  it('falls back to the list for an unknown section instead of rendering an empty page', async () => {
    build('/procurement/customs-prices/khong-co?q=abc')
    await waitFor(() => expect(currentLocation()).toBe('/procurement/customs-prices?q=abc'))
  })

  it('sends a typed /config URL back to the list when the user has neither config right', async () => {
    canManageConfig = false
    canWrite = false
    canReadRegulations = false
    build('/procurement/customs-prices/config')
    await waitFor(() => expect(currentLocation()).toBe('/procurement/customs-prices'))
  })

  it('opens /config for a user who can only READ the chemical list', async () => {
    canManageConfig = false
    canWrite = false
    build('/procurement/customs-prices/config')
    expect(await screen.findByRole('heading', { name: /Cấu hình/ })).toBeInTheDocument()
    expect(currentLocation()).toBe('/procurement/customs-prices/config')
  })

  //  01/10/2026 — năm mục tra giá về lại dạng THẺ (menu trái chỉ còn một mục cho cả năm):
  //  bấm thẻ phải đổi đường VÀ giữ bộ lọc, như lúc chưa tách submenu.
  it('shows the five price tabs and switches section keeping the filters', async () => {
    build('/procurement/customs-prices?origin=CN')
    const tabs = await screen.findAllByRole('tab')
    expect(tabs.map((tab) => tab.textContent)).toEqual([
      'Danh sách',
      'Biểu đồ',
      'Doanh nghiệp',
      'So sánh',
      'Thuế',
    ])
    await userEvent.click(screen.getByRole('tab', { name: 'Thuế' }))
    await waitFor(() =>
      expect(currentLocation()).toBe('/procurement/customs-prices/tariff?origin=CN'),
    )
    expect(screen.getByRole('tab', { name: 'Thuế' })).toHaveAttribute('aria-selected', 'true')
  })

  it('keeps Pháp lý as its own submenu page without the price tabs', async () => {
    build('/procurement/customs-prices/legal')
    expect(await screen.findByRole('heading', { name: /Pháp lý/ })).toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: 'Danh sách' })).not.toBeInTheDocument()
  })

  it('keeps the filters when the header button jumps to the import history', async () => {
    build('/procurement/customs-prices?origin=CN')
    ;(await screen.findByRole('button', { name: /Lịch sử nạp/ })).click()
    await waitFor(() =>
      expect(currentLocation()).toBe('/procurement/customs-prices/history?origin=CN'),
    )
  })
})
