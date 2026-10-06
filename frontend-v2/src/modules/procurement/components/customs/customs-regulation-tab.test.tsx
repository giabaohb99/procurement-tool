// Mục «Pháp lý»: bảng duyệt cả danh mục hóa chất theo văn bản + thẻ cảnh báo của từ khóa đang
// tra. Chặn ở tầng `@/core/api` (luật testing.md).
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
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
    seq_no: '',
    name: 'Toluene',
    name_vi: '',
    cas_no: '108-88-3',
    formula: '',
    category: '',
    threshold_kg: 1000,
    mixture_pct: null,
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

  //  duoc-CR-598 — bảng theo đúng các cột của phụ lục NĐ 24: STT · Tên khoa học · Tên chất ·
  //  Mã số CAS · Công thức hóa học, mỗi thứ một cột (trước đây tên Việt chỉ là dòng phụ).
  it('shows the appendix columns STT, scientific name, chemical name, CAS and formula separately', async () => {
    items = [
      hit({
        seq_no: '59',
        name: 'Barium hypochlorite',
        name_vi: 'Bari hypoclorit',
        cas_no: '13477-10-6',
        formula: 'Ba(ClO)2',
        list_label: 'NĐ 24/2026 · Phụ lục II',
      }),
    ]
    build()
    expect(await screen.findByText('Barium hypochlorite')).toBeInTheDocument()
    for (const header of ['STT', 'Tên khoa học', 'Tên chất', 'Mã số CAS', 'Công thức hóa học']) {
      expect(screen.getByRole('columnheader', { name: new RegExp(header) })).toBeInTheDocument()
    }
    const row = screen.getByRole('row', { name: /Barium hypochlorite/ })
    for (const cell of ['59', 'Bari hypoclorit', '13477-10-6', 'Ba(ClO)2']) {
      expect(within(row).getByText(cell)).toBeInTheDocument()
    }
  })

  it('leaves the new cells blank for documents that have no STT or formula', async () => {
    items = [hit({ list_code: 10, list_label: 'TT 75/2025 · Hoạt chất cấm', name: 'Paraquat', threshold_kg: null })]
    build()
    const row = await screen.findByRole('row', { name: /Paraquat/ })
    expect(within(row).queryByText('undefined')).not.toBeInTheDocument()
    expect(within(row).queryByText('null')).not.toBeInTheDocument()
  })

  //  duoc-CR-598 — ô trống bị đọc thành «thiếu dữ liệu». PL IV có ngưỡng TỒN TRỮ kg; PL II / III có
  //  ngưỡng HÀM LƯỢNG hỗn hợp % (câu ghi chú của NĐ 24, tệp Excel không có); PL I không có ngưỡng nào.
  it('fills the limit cell with kg, the mixture percentage, or says there is none', async () => {
    items = [
      hit({ id: 1, list_code: 1, list_label: 'NĐ 24/2026 · Phụ lục I', name: 'Argon', threshold_kg: null }),
      hit({ id: 5, list_code: 2, list_label: 'NĐ 24/2026 · Phụ lục II', name: 'Acetaldehyde', threshold_kg: null, mixture_pct: 5 }),
      hit({ id: 6, list_code: 3, list_label: 'NĐ 24/2026 · Phụ lục III', name: 'Phosgene', threshold_kg: null, mixture_pct: 1 }),
      hit({ id: 2, list_code: 4, name: 'Potassium nitrate', threshold_kg: null }),
      hit({ id: 3, list_code: 4, name: 'Potassium nitrate — Dạng hạt', threshold_kg: 5000000 }),
      hit({ id: 4, list_code: 11, list_label: 'TT 01/2026', name: 'Benzene', threshold_kg: null }),
    ]
    build()
    const argon = await screen.findByRole('row', { name: /Argon/ })
    expect(within(argon).getByText('Không quy định ngưỡng')).toBeInTheDocument()
    expect(within(screen.getByRole('row', { name: /Acetaldehyde/ })).getByText('> 5% trong hỗn hợp')).toBeInTheDocument()
    expect(within(screen.getByRole('row', { name: /Phosgene/ })).getByText('> 1% trong hỗn hợp')).toBeInTheDocument()
    expect(
      within(screen.getByRole('row', { name: /^.*Potassium nitrate(?! —)/ })).getByText('Theo từng dạng / hàm lượng'),
    ).toBeInTheDocument()
    expect(within(screen.getByRole('row', { name: /Dạng hạt/ })).getByText(/5\.000\.000/)).toBeInTheDocument()
    const benzene = screen.getByRole('row', { name: /Benzene/ })
    expect(within(benzene).queryByText(/ngưỡng|hàm lượng|hỗn hợp/)).not.toBeInTheDocument()
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
