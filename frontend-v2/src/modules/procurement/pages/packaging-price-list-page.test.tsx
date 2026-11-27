// bao-CR-800 — trạng thái lọc / xếp / trang của Bảng giá VTBB được tách ra hook dùng chung với Bảng giá nguyên liệu
// (`usePackagingPriceListState`). Bài kiểm này giữ nguyên hành vi của màn VTBB sau khi tách: vẫn gọi đường của VTBB, vẫn gửi
// `scope`, vẫn có nút phạm vi + cột Số SP đang dùng, và KHÔNG lỡ tay gọi sang đường của nguyên liệu.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'

import type { PackagingPriceListResult, PackagingPriceRow } from '../types/packaging-cost-types'
import { PackagingPriceListPage } from './packaging-price-list-page'

const LIST_URL = '/api/packaging-cost/price-list'
const OPTIONS_URL = '/api/packaging-cost/code-options'

const calls: { url: string; params?: Record<string, unknown> }[] = []
const downloads: { url: string; params?: Record<string, unknown> }[] = []
let granted: string[] = []

const row: PackagingPriceRow = {
  code: 'CET0028',
  name: 'Chai PAPE tròn cổ 43',
  group: 'Chai',
  unit: 'Cái',
  purchase_count: 3,
  last_date: '2026-06-30',
  last_purchase_price: 3170,
  last_purchase_date: '2026-06-30',
  prev_purchase_price: 4300,
  quote: null,
  old: 4300,
  new: 3170,
  diff: -1130,
  pct: -0.2628,
  usage: 30,
  min: 3170,
  max: 4724,
  warnings: [],
}
const result: PackagingPriceListResult = { items: [row], total: 1 }

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    apiGet: async (url: string, config?: { params?: Record<string, unknown> }) => {
      calls.push({ url, params: config?.params })
      if (url === LIST_URL) return result
      if (url === OPTIONS_URL) {
        return { items: [{ code: 'CET0028', name: 'Chai PAPE tròn cổ 43', group: 'Chai', usage: 30, new: 3170 }] }
      }
      throw new Error(`403 ${url}`)
    },
    downloadFile: async (url: string, _name: string, params?: Record<string, unknown>) => {
      downloads.push({ url, params })
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
      <MemoryRouter initialEntries={[`/procurement/packaging-cost/prices${search}`]}>
        <PackagingPriceListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const listCalls = () => calls.filter((call) => call.url === LIST_URL)
const lastListParams = () => listCalls().at(-1)?.params

beforeEach(() => {
  calls.length = 0
  downloads.length = 0
  localStorage.clear()
  granted = ['packaging_price_list.read', 'packaging_price_list.export']
})

describe('PackagingPriceListPage', () => {
  it('still loads the VTBB price list with scope=bom and the "all" code options, never the material endpoints', async () => {
    build()
    expect(await screen.findByText('Chai PAPE tròn cổ 43')).toBeInTheDocument()
    expect(listCalls()[0].params).toMatchObject({ scope: 'bom', page: 1, page_size: 50 })
    await waitFor(() =>
      expect(calls.find((call) => call.url === OPTIONS_URL)?.params).toEqual({ scope: 'all' }),
    )
    expect(calls.some((call) => call.url.includes('material'))).toBe(false)
    expect(screen.getByText('Mã VTBB')).toBeInTheDocument()
    expect(screen.getByText('Số SP đang dùng')).toBeInTheDocument()
  })

  it('keeps the scope toggle: "Mọi mã có giá" sends scope=all, counts as a filter, and Xóa lọc returns to bom', async () => {
    const user = userEvent.setup()
    build()
    await screen.findByText('Chai PAPE tròn cổ 43')
    await user.click(screen.getByRole('radio', { name: 'Mọi mã có giá' }))
    await waitFor(() => expect(lastListParams()).toMatchObject({ scope: 'all', page: 1 }))
    await user.click(screen.getByRole('button', { name: /Xóa lọc/ }))
    await waitFor(() => expect(lastListParams()).toMatchObject({ scope: 'bom' }))
  })

  it('reopens from a link with scope and the usage sort, and exports with them but without the page', async () => {
    const user = userEvent.setup()
    build('?scope=all&sort_by=usage&sort_dir=desc&group=Chai')
    await screen.findByText('Chai PAPE tròn cổ 43')
    expect(listCalls()[0].params).toMatchObject({
      scope: 'all',
      group: 'Chai',
      sort_by: 'usage',
      sort_dir: 'desc',
    })
    await user.click(screen.getByRole('button', { name: /Xuất Excel/ }))
    await waitFor(() => expect(downloads).toHaveLength(1))
    expect(downloads[0].url).toBe('/api/packaging-cost/price-list/export')
    expect(downloads[0].params).toMatchObject({ scope: 'all', group: 'Chai', sort_by: 'usage', sort_dir: 'desc' })
    expect(downloads[0].params).not.toHaveProperty('page')
  })

  it('does not show Xuất Excel to someone holding only the material export right', async () => {
    granted = ['packaging_price_list.read', 'packaging_material_price.export']
    build()
    await screen.findByText('Chai PAPE tròn cổ 43')
    expect(screen.queryByRole('button', { name: /Xuất Excel/ })).not.toBeInTheDocument()
  })
})
