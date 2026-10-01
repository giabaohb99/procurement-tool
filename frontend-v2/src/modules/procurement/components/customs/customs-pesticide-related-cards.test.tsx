// Hai khối «cùng công ty» / «cùng hoạt chất» của trang chi tiết thuốc BVTV (01/10/2026). Chặn ở
// tầng `@/core/api` (luật testing.md) để khẳng định đúng tham số `limit` gửi đi.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'

import type { CustomsPesticideBrief, CustomsPesticideRelated } from '../../types/customs-pesticide'
import { CustomsPesticideRelatedCards } from './customs-pesticide-related-cards'

const calls: { url: string; params?: Record<string, unknown> }[] = []
let response: CustomsPesticideRelated

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    apiGet: vi.fn(async (url: string, config?: { params?: Record<string, unknown> }) => {
      calls.push({ url, params: config?.params })
      const limit = Number(config?.params?.limit ?? 300)
      return {
        same_registrant: {
          ...response.same_registrant,
          items: response.same_registrant.items.slice(0, limit),
        },
        same_ingredient: {
          ...response.same_ingredient,
          items: response.same_ingredient.items.slice(0, limit),
        },
      }
    }),
  }
})

function brief(id: number, over: Partial<CustomsPesticideBrief> = {}): CustomsPesticideBrief {
  return {
    id,
    trade_name: `Thuốc ${String(id).padStart(2, '0')}`,
    pest_group: 'Thuốc trừ bệnh',
    active_ingredient: 'Chitosan 2% + Oligo-Alginate 10%',
    registrant: 'Công ty TNHH Ngân Anh',
    status: 1,
    status_label: 'Còn hiệu lực',
    ...over,
  }
}

function LocationProbe() {
  const { pathname } = useLocation()
  return <output aria-label="location">{pathname}</output>
}

function renderCards(registrant = 'Công ty TNHH Ngân Anh') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/procurement/customs-prices/pesticides/13841']}>
        <Routes>
          <Route
            path="*"
            element={<CustomsPesticideRelatedCards pesticideId={13841} registrant={registrant} />}
          />
        </Routes>
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/** Tên thuốc đang hiện trong bảng (mỗi dòng một tên "Thuốc NN"). */
function visibleNames() {
  return screen.queryAllByText(/^Thuốc \d+$/).map((el) => el.textContent)
}

beforeEach(() => {
  calls.length = 0
  response = {
    same_registrant: { total: 31, items: Array.from({ length: 31 }, (_, i) => brief(i + 1)) },
    same_ingredient: { label: 'Chitosan + Oligo-Alginate', total: 1, items: [brief(99)] },
  }
})

describe('CustomsPesticideRelatedCards', () => {
  it('fetches once with the large limit and shows the first page of the company tab', async () => {
    renderCards()
    await screen.findByText('Thuốc 01')
    expect(calls).toEqual([
      { url: '/api/customs/pesticides/13841/related', params: { limit: 300 } },
    ])
    expect(screen.getByRole('radio', { name: /Cùng công ty\s*31/ })).toHaveAttribute(
      'aria-checked',
      'true',
    )
    expect(screen.getByRole('radio', { name: /Cùng hoạt chất\s*1/ })).toBeInTheDocument()
    expect(visibleNames()).toHaveLength(10)
    expect(screen.getByText('Công ty TNHH Ngân Anh')).toBeInTheDocument()
    //  Tab công ty KHÔNG có cột công ty — trùng nhau ở mọi dòng.
    expect(screen.queryByText('Công ty đăng ký')).not.toBeInTheDocument()
  })

  it('pages through every item without calling the API again', async () => {
    renderCards()
    await screen.findByText('Thuốc 01')
    await userEvent.click(screen.getByRole('button', { name: 'Trang 4' }))
    expect(await screen.findByText('Thuốc 31')).toBeInTheDocument()
    expect(visibleNames()).toEqual(['Thuốc 31'])
    expect(calls).toHaveLength(1)
  })

  it('switches to the ingredient tab with the company column and the stripped label', async () => {
    renderCards()
    await screen.findByText('Thuốc 01')
    await userEvent.click(screen.getByRole('radio', { name: /Cùng hoạt chất/ }))
    expect(await screen.findByText('Chitosan + Oligo-Alginate')).toBeInTheDocument()
    expect(screen.getByText('Công ty đăng ký')).toBeInTheDocument()
    expect(visibleNames()).toEqual(['Thuốc 99'])
  })

  it('opens the clicked pesticide detail page', async () => {
    renderCards()
    await userEvent.click(await screen.findByText('Thuốc 05'))
    await waitFor(() =>
      expect(screen.getByRole('status', { name: 'location' })).toHaveTextContent(
        '/procurement/customs-prices/pesticides/5',
      ),
    )
  })

  it('flags only items that are no longer active', async () => {
    response.same_registrant.items[0] = brief(1, { status: 3, status_label: 'Hết hiệu lực' })
    renderCards()
    expect(await screen.findByText('Hết hiệu lực')).toBeInTheDocument()
    expect(screen.queryByText('Còn hiệu lực')).not.toBeInTheDocument()
  })

  //  Công ty chỉ có đúng thuốc này: đừng mở ra một tab rỗng khi tab kia có thuốc.
  it('opens the ingredient tab first when the company has no other product', async () => {
    response.same_registrant = { total: 0, items: [] }
    renderCards()
    expect(await screen.findByText('Thuốc 99')).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: /Cùng hoạt chất/ })).toHaveAttribute(
      'aria-checked',
      'true',
    )
  })

  it('says so when both groups are empty and still names the company', async () => {
    response = {
      same_registrant: { total: 0, items: [] },
      same_ingredient: { label: '', total: 0, items: [] },
    }
    renderCards('Công ty Một Thuốc')
    expect(
      await screen.findByText('Công ty này chưa có thuốc nào khác trong danh mục.'),
    ).toBeInTheDocument()
    expect(screen.getByText('Công ty Một Thuốc')).toBeInTheDocument()
  })
})
