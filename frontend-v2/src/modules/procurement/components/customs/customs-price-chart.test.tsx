// duoc-CR-744 — bảng kỳ dưới biểu đồ giá (Giá thị trường > Biểu đồ) xếp được theo từng cột: kỳ không có dòng nào
// hiện "—" nên luôn xuống cuối ở cả hai chiều; cột Kỳ xếp theo thời gian thật chứ không theo nhãn chữ.
// Chặn ở tầng `@/core/api` (luật testing.md).
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'

import type { CustomsFilters } from '../../types/customs'
import { CustomsPriceChart } from './customs-price-chart'

function point(period: string, label: string, count: number, wavg: number | null, qty = 0) {
  return {
    period,
    label,
    count,
    qty,
    min: wavg === null ? null : wavg - 1,
    max: wavg === null ? null : wavg + 1,
    p25: wavg === null ? null : wavg - 0.5,
    p75: wavg === null ? null : wavg + 0.5,
    wavg,
    low_data: false,
  }
}

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    apiGet: async (url: string) => {
      if (url.endsWith('/stats')) {
        return {
          period: 'month',
          price_mode: 'adjusted',
          unit: 'KGM',
          units: [{ unit: 'KGM', count: 14 }],
          series: [
            point('2025-12', '12/2025', 5, 3, 100),
            point('2026-01', '01/2026', 0, null),
            point('2026-02', '02/2026', 9, 7, 40),
          ],
          kpi: { count: 14, qty: 140, min: 2, max: 8, wavg: 5, outliers: 0 },
          best_period: null,
          min_lines_for_best: 5,
          coverage: { lines: 14, months: 3, years: 2, date_from: null, date_to: null, empty_periods: [] },
        }
      }
      throw new Error(`Không mock đường ${url}`)
    },
  }
})

function build() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <CustomsPriceChart filters={{ hs_code: '3808' } as unknown as CustomsFilters} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/** Nhãn kỳ theo thứ tự dòng của BẢNG (bảng nằm cuối trang, sau các biểu đồ). */
function shownPeriods() {
  const tbody = screen.getAllByRole('rowgroup').at(-1) as HTMLElement
  return within(tbody)
    .getAllByRole('row')
    .map((row) => within(row).getAllByRole('cell')[0]?.textContent ?? '')
}

const header = (text: string | RegExp) => screen.findByText(text, { selector: 'thead span' })

describe('CustomsPriceChart — sắp xếp bảng kỳ', () => {
  it('lists the periods oldest first until a header is clicked', async () => {
    build()
    await header('Kỳ')
    await waitFor(() => expect(shownPeriods()).toEqual(['12/2025', '01/2026', '02/2026']))
  })

  it('sorts the period column by real time, not by the "MM/YYYY" label text', async () => {
    const user = userEvent.setup()
    build()
    await user.click(await header('Kỳ'))
    //  Nhãn chữ "01/2026" < "02/2026" < "12/2025" nếu xếp theo chữ — sai thời gian.
    await waitFor(() => expect(shownPeriods()).toEqual(['12/2025', '01/2026', '02/2026']))
    await user.click(await header('Kỳ'))
    await waitFor(() => expect(shownPeriods()).toEqual(['02/2026', '01/2026', '12/2025']))
  })

  it('keeps the empty period (shown as a dash) last in both directions of a price column', async () => {
    const user = userEvent.setup()
    build()
    await user.click(await header('Bình quân gia quyền'))
    await waitFor(() => expect(shownPeriods()).toEqual(['02/2026', '12/2025', '01/2026']))
    await user.click(await header('Bình quân gia quyền'))
    await waitFor(() => expect(shownPeriods()).toEqual(['12/2025', '02/2026', '01/2026']))
    await user.click(await header('Bình quân gia quyền'))
    await waitFor(() => expect(shownPeriods()).toEqual(['12/2025', '01/2026', '02/2026']))
  })
})
