// Mục «Pháp lý»: bảng duyệt cả danh mục hóa chất theo văn bản + thẻ cảnh báo của từ khóa đang
// tra. Chặn ở tầng `@/core/api` (luật testing.md).
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'

import type { CustomsRegulationHit } from '../../types/customs'
import { CustomsRegulationTab } from './customs-regulation-tab'

const calls: { url: string; params?: Record<string, unknown> }[] = []
let catalogTotal = 2
let items: CustomsRegulationHit[] = []

function hit(over: Partial<CustomsRegulationHit>): CustomsRegulationHit {
  return {
    id: 1,
    list_code: 4,
    list_label: 'NĐ 24/2026 · Phụ lục IV',
    name: 'Toluene',
    name_vi: '',
    cas_no: '108-88-3',
    category: '',
    threshold_kg: 1000,
    banned_year: null,
    legal_basis: 'NĐ 24/2026/NĐ-CP',
    note: '',
    obligation: 'Có NGƯỠNG KHỐI LƯỢNG 1000 kg theo NĐ 24/2026/NĐ-CP.',
    ...over,
  }
}

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    apiGet: async (url: string, config?: { params?: Record<string, unknown> }) => {
      calls.push({ url, params: config?.params })
      if (url.endsWith('/regulations/options')) {
        return { total: catalogTotal, lists: [{ value: 10, label: 'TT 75/2025 · Hoạt chất cấm', count: 1 }] }
      }
      if (url.endsWith('/regulations')) return { total: items.length, items }
      if (url.endsWith('/pesticides')) {
        return {
          total: 1,
          items: [
            {
              id: 11,
              trade_name: 'Lọt Lưới 480EC',
              active_ingredient: 'Chlorpyrifos Ethyl 480g/l',
              registrant: 'Công ty A',
              registration_no: '1/CNĐKT-BVTV',
              status: 2,
              status_label: 'Hết hiệu lực',
              banned: [{ id: 9, name: 'Chlorpyrifos ethyl', cas_no: '', banned_year: 2019, legal_basis: '' }],
            },
          ],
        }
      }
      throw new Error(`Không mock đường ${url}`)
    },
  }
})

function build(props: { keyword?: string; alerts?: CustomsRegulationHit[] } = {}) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <CustomsRegulationTab keyword={props.keyword ?? ''} alerts={props.alerts ?? []} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  calls.length = 0
  catalogTotal = 2
  items = []
  localStorage.clear()
})

describe('CustomsRegulationTab', () => {
  it('loads every document on page 1 without a list filter by default', async () => {
    build()
    await waitFor(() => expect(calls.some((call) => call.url.endsWith('/regulations'))).toBe(true))
    const list = calls.find((call) => call.url.endsWith('/regulations'))
    expect(list?.params).toEqual({ page: 1, page_size: 50 })
  })

  it('shows the threshold of a chemical in the browse table', async () => {
    items = [hit({})]
    build()
    expect(await screen.findByText('Toluene')).toBeInTheDocument()
    expect(screen.getByText('NĐ 24/2026 · Phụ lục IV')).toBeInTheDocument()
  })

  it('shows the keyword alerts card only when the current keyword hits something', async () => {
    const { unmount } = build({ keyword: 'paraquat', alerts: [hit({ id: 9, list_code: 10, name: 'Paraquat' })] })
    expect(await screen.findByText('Cảnh báo cho từ khóa đang tra «paraquat»')).toBeInTheDocument()
    unmount()
    build({ keyword: 'paraquat', alerts: [] })
    await screen.findByText(/khớp/)
    expect(screen.queryByText(/Cảnh báo cho từ khóa/)).not.toBeInTheDocument()
  })

  it('says the catalog is empty instead of blaming the filter', async () => {
    catalogTotal = 0
    build()
    expect(await screen.findByText(/Chưa có danh mục hóa chất theo văn bản/)).toBeInTheDocument()
  })

  it('searches by the typed keyword and resets it with «Xóa lọc»', async () => {
    build()
    const search = await screen.findByRole('textbox', { name: 'Tìm hóa chất theo văn bản' })
    fireEvent.change(search, { target: { value: 'H2SO4' } })
    await waitFor(() => {
      const last = calls.filter((call) => call.url.endsWith('/regulations')).at(-1)
      expect(last?.params).toMatchObject({ q: 'H2SO4', page: 1 })
    })
    fireEvent.click(screen.getByRole('button', { name: /Xóa lọc/ }))
    expect(search).toHaveValue('')
  })

  describe('cột «Thuốc BVTV chứa»', () => {
    const banned = (over: Partial<CustomsRegulationHit>) =>
      hit({ id: 9, list_code: 10, list_label: 'TT 75/2025 · Hoạt chất cấm', name: 'Chlorpyrifos ethyl',
        threshold_kg: null, banned_year: 2019, legal_basis: 'TT 75/2025/TT-BNNMT', ...over })

    it('shows nothing for rows that are not banned ingredients', async () => {
      items = [hit({ pesticide_count: null })]
      build()
      await screen.findByText('Toluene')
      expect(screen.queryByText(/Chưa nạp danh mục thuốc/)).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /thuốc$/ })).not.toBeInTheDocument()
    })

    //  «0» khi chưa nạp danh mục thuốc sẽ đọc thành «đã đối chiếu, sạch» — sai.
    it('says the pesticide catalog is not loaded instead of showing 0', async () => {
      items = [banned({ pesticide_count: null })]
      build()
      expect(await screen.findByText('Chưa nạp danh mục thuốc')).toBeInTheDocument()
    })

    it('shows a plain 0 that opens nothing when no drug contains it', async () => {
      items = [banned({ pesticide_count: 0 })]
      build()
      expect(await screen.findByText('0')).toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /thuốc$/ })).not.toBeInTheDocument()
    })

    it('opens the drugs containing the banned ingredient, across every status', async () => {
      items = [banned({ pesticide_count: 1 })]
      build()
      fireEvent.click(await screen.findByRole('button', { name: '1 thuốc' }))
      expect(await screen.findByRole('dialog', { name: 'Thuốc BVTV chứa Chlorpyrifos ethyl' })).toBeInTheDocument()
      expect(await screen.findByText('Lọt Lưới 480EC')).toBeInTheDocument()
      const call = calls.filter((c) => c.url.endsWith('/pesticides')).at(-1)
      expect(call?.params).toEqual({ banned_regulation_id: 9, page: 1, page_size: 50 })
      expect(call?.params).not.toHaveProperty('status')
    })
  })
})
