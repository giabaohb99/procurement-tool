// bao-CR-800 — màn Bảng giá nguyên liệu: dữ liệu thật qua ba đường RIÊNG của nguyên liệu (khóa `packaging_material_price`).
// Người chỉ giữ khóa này gọi `price-list` / `code-options` của VTBB là 403, nên bài kiểm canh chặt: màn KHÔNG được gọi hai
// đường đó dưới bất kỳ thao tác nào. Chặn ở tầng `@/core/api` (luật testing.md) để bắt đúng đường + tham số màn gửi đi.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'

import type {
  PackagingCodeOption,
  PackagingPriceListResult,
  PackagingPriceRow,
} from '../types/packaging-cost-types'
import { PackagingMaterialPriceListPage } from './packaging-material-price-list-page'

const LIST_URL = '/api/packaging-cost/material-price-list'
const OPTIONS_URL = '/api/packaging-cost/material-code-options'
const EXPORT_URL = '/api/packaging-cost/material-price-list/export'

const calls: { url: string; params?: Record<string, unknown> }[] = []
const downloads: { url: string; name: string; params?: Record<string, unknown> }[] = []
let granted: string[] = []
let result: PackagingPriceListResult = { items: [], total: 0 }
let options: PackagingCodeOption[] = []

const row = (over: Partial<PackagingPriceRow> = {}): PackagingPriceRow => ({
  code: 'NL0001',
  name: 'Hoạt chất Abamectin 95%',
  group: 'Nguyên liệu',
  unit: 'Kg',
  purchase_count: 4,
  last_date: '2026-10-12',
  last_purchase_price: 1250000,
  last_purchase_date: '2026-10-12',
  prev_purchase_price: 1200000,
  quote: null,
  old: 1200000,
  new: 1250000,
  diff: 50000,
  pct: 0.0417,
  usage: 0,
  min: 1150000,
  max: 1300000,
  warnings: [],
  ...over,
})

const option = (code: string, group: string): PackagingCodeOption => ({
  code,
  name: `Tên ${code}`,
  group,
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
      //  Mọi đường khác (nhất là hai đường của VTBB) coi như bị cấm — đúng cái người chỉ giữ khóa nguyên liệu gặp.
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

function build(search = '') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/procurement/packaging-cost/material-prices${search}`]}>
        <PackagingMaterialPriceListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const listCalls = () => calls.filter((call) => call.url === LIST_URL)
const lastListParams = () => listCalls().at(-1)?.params
const picker = () => screen.getByRole('combobox', { name: 'Chọn mã nguyên liệu' })

beforeEach(() => {
  calls.length = 0
  downloads.length = 0
  localStorage.clear()
  granted = ['packaging_material_price.read', 'packaging_material_price.export']
  result = {
    items: [row(), row({ code: 'NL0002', name: 'Dung môi Xylene', group: 'Dung môi', quote: { price: 31000, valid_from: '2026-11-20' } })],
    total: 2,
  }
  options = [option('NL0001', 'Nguyên liệu'), option('NL0002', 'Dung môi'), option('NL0003', 'Nguyên liệu')]
})

describe('PackagingMaterialPriceListPage', () => {
  it('loads from the material endpoints only and never touches the VTBB price-list or code-options', async () => {
    const user = userEvent.setup()
    build()
    expect(await screen.findByText('Hoạt chất Abamectin 95%')).toBeInTheDocument()
    await waitFor(() => expect(picker()).toBeEnabled())
    //  Đi qua mọi thao tác gọi máy chủ: chip nhóm, xếp cột, chọn mã, xuất.
    await user.click(screen.getByRole('button', { name: 'Dung môi' }))
    await user.click(screen.getByText('Giá mới'))
    await user.click(picker())
    await user.click(await screen.findByRole('option', { name: /NL0003/ }))
    await user.click(screen.getByRole('button', { name: /Xuất Excel/ }))
    await waitFor(() => expect(downloads).toHaveLength(1))

    expect(new Set(calls.map((call) => call.url))).toEqual(new Set([LIST_URL, OPTIONS_URL]))
    expect(downloads[0].url).toBe(EXPORT_URL)
    expect(calls.find((call) => call.url === OPTIONS_URL)?.params).toBeUndefined()
  })

  it('asks for page 1 of 50 with no scope — the material endpoint has no "in BOM" notion', async () => {
    build()
    await screen.findByText('Hoạt chất Abamectin 95%')
    expect(listCalls()[0].params).toMatchObject({ page: 1, page_size: 50 })
    for (const key of ['scope', 'sort_by', 'sort_dir']) expect(listCalls()[0].params).not.toHaveProperty(key)
    expect(listCalls()[0].params?.code).toBeUndefined()
    expect(listCalls()[0].params?.group).toBeUndefined()
    //  Nút phạm vi của màn VTBB không có nghĩa với nguyên liệu.
    expect(screen.queryByRole('group', { name: 'Phạm vi mã' })).not.toBeInTheDocument()
    expect(screen.queryByText('Mã trong định mức')).not.toBeInTheDocument()
    expect(screen.queryByText('Mọi mã có giá')).not.toBeInTheDocument()
  })

  it('shows the material columns: plain-text codes, no "Số SP đang dùng", no quote action', async () => {
    //  Kể cả người có quyền Lịch sử mua hàng + tạo báo giá VTBB: màn lịch sử của cụm không còn mã nguyên liệu.
    granted.push('packaging_history.read', 'packaging_price_list.create')
    build()
    const line = (await screen.findByText('Hoạt chất Abamectin 95%')).closest('tr') as HTMLTableRowElement
    expect(within(line).getByText('NL0001')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /NL000/ })).not.toBeInTheDocument()
    expect(screen.getByText('Mã nguyên liệu')).toBeInTheDocument()
    expect(screen.getByText('Tên nguyên liệu')).toBeInTheDocument()
    for (const header of ['Mã VTBB', 'Tên vật tư', 'Số SP đang dùng', 'Thao tác']) {
      expect(screen.queryByText(header)).not.toBeInTheDocument()
    }
    expect(screen.queryByRole('button', { name: 'Báo giá' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Báo giá mới/ })).not.toBeInTheDocument()
    expect(within(line).getByText('+50.000')).toBeInTheDocument()
  })

  it('sends the group chip, the picked codes and the clicked sort column to the server', async () => {
    const user = userEvent.setup()
    build()
    await screen.findByText('Hoạt chất Abamectin 95%')
    //  Chip nhóm lấy từ chính danh sách mã nguyên liệu, giữ thứ tự của danh sách đã xếp.
    const chips = within(screen.getByRole('group', { name: 'Lọc theo nhóm' })).getAllByRole('button')
    expect(chips.map((chip) => chip.textContent)).toEqual(['Tất cả', 'Nguyên liệu', 'Dung môi'])

    await user.click(screen.getByRole('button', { name: 'Nguyên liệu' }))
    await waitFor(() => expect(lastListParams()).toMatchObject({ group: 'Nguyên liệu', page: 1 }))

    await user.click(picker())
    await user.click(await screen.findByRole('option', { name: /NL0003/ }))
    await user.click(screen.getByRole('option', { name: /NL0001/ }))
    await waitFor(() =>
      expect(lastListParams()).toMatchObject({ group: 'Nguyên liệu', code: ['NL0003', 'NL0001'] }),
    )
    await user.keyboard('{Escape}')

    await user.click(screen.getByText('Giá mới'))
    await waitFor(() => expect(lastListParams()).toMatchObject({ sort_by: 'new', sort_dir: 'asc' }))
    await user.click(screen.getByText('Giá mới'))
    await waitFor(() =>
      expect(lastListParams()).toMatchObject({
        group: 'Nguyên liệu',
        code: ['NL0003', 'NL0001'],
        sort_by: 'new',
        sort_dir: 'desc',
        page: 1,
        page_size: 50,
      }),
    )
    expect(lastListParams()).not.toHaveProperty('scope')
  })

  it('pages on the server and goes back to page 1 when a filter changes', async () => {
    const user = userEvent.setup()
    result = { items: result.items, total: 120 }
    build()
    await screen.findByText('Hoạt chất Abamectin 95%')
    await user.click(screen.getByRole('button', { name: 'Trang sau' }))
    await waitFor(() => expect(lastListParams()).toMatchObject({ page: 2, page_size: 50 }))
    await user.click(screen.getByRole('button', { name: 'Dung môi' }))
    await waitFor(() => expect(lastListParams()).toMatchObject({ group: 'Dung môi', page: 1 }))
  })

  it('reopens from a link with its date range, codes, sort and page — dropping scope and the usage sort', async () => {
    result = { items: result.items, total: 120 }
    build('?code=NL0002&code=NL0001&date_from=2026-01-01&date_to=2026-06-30&sort_by=old&sort_dir=desc&page=2&scope=all')
    await screen.findByText('Hoạt chất Abamectin 95%')
    expect(listCalls()[0].params).toMatchObject({
      code: ['NL0002', 'NL0001'],
      date_from: '2026-01-01',
      date_to: '2026-06-30',
      sort_by: 'old',
      sort_dir: 'desc',
      page: 2,
    })
    expect(listCalls()[0].params).not.toHaveProperty('scope')
  })

  it('ignores a crafted sort_by=usage (the column does not exist here) and a reversed date range', async () => {
    build('?sort_by=usage&sort_dir=desc&date_from=2026-06-30&date_to=2026-01-01')
    await screen.findByText('Hoạt chất Abamectin 95%')
    for (const key of ['sort_by', 'sort_dir', 'scope']) expect(listCalls()[0].params).not.toHaveProperty(key)
    expect(listCalls()[0].params?.date_from).toBeUndefined()
    expect(listCalls()[0].params?.date_to).toBeUndefined()
  })

  it('exports with the same filters and order, without page, to the material export endpoint', async () => {
    const user = userEvent.setup()
    build('?date_from=2026-01-01&date_to=2026-06-30')
    await screen.findByText('Hoạt chất Abamectin 95%')
    await user.click(screen.getByRole('button', { name: 'Dung môi' }))
    await user.click(screen.getByText('Số lần mua'))
    await waitFor(() => expect(lastListParams()).toMatchObject({ sort_by: 'purchase_count', sort_dir: 'desc' }))
    await user.click(screen.getByRole('button', { name: /Xuất Excel/ }))
    await waitFor(() => expect(downloads).toHaveLength(1))
    expect(downloads[0]).toMatchObject({ url: EXPORT_URL, name: 'bang-gia-nguyen-lieu.xlsx' })
    expect(downloads[0].params).toMatchObject({
      group: 'Dung môi',
      date_from: '2026-01-01',
      date_to: '2026-06-30',
      sort_by: 'purchase_count',
      sort_dir: 'desc',
    })
    for (const key of ['page', 'page_size', 'scope']) expect(downloads[0].params).not.toHaveProperty(key)
  })

  it('shows Xuất Excel only with packaging_material_price.export — the VTBB export right does not count', async () => {
    granted = ['packaging_material_price.read', 'packaging_price_list.export', 'packaging_price_list.read']
    const first = build()
    await screen.findByText('Hoạt chất Abamectin 95%')
    expect(screen.queryByRole('button', { name: /Xuất Excel/ })).not.toBeInTheDocument()
    first.unmount()

    granted = ['packaging_material_price.read', 'packaging_material_price.export']
    build()
    await screen.findByText('Hoạt chất Abamectin 95%')
    expect(screen.getByRole('button', { name: /Xuất Excel/ })).toBeInTheDocument()
  })

  it('says no material has a price when unfiltered, and "no match" once a filter is on; Xóa lọc clears it', async () => {
    const user = userEvent.setup()
    result = { items: [], total: 0 }
    //  `scope=all` trên URL không phải bộ lọc của màn này — vẫn là câu rỗng "chưa có".
    build('?scope=all')
    expect(await screen.findByText('Chưa có nguyên liệu nào có giá.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Xóa lọc/ })).not.toBeInTheDocument()

    await user.click(await screen.findByRole('button', { name: 'Dung môi' }))
    expect(await screen.findByText('Không có mã nào khớp bộ lọc.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /Xóa lọc/ }))
    expect(await screen.findByText('Chưa có nguyên liệu nào có giá.')).toBeInTheDocument()
    await waitFor(() => expect(lastListParams()?.group).toBeUndefined())
  })

  it('still renders an empty picker and the "Tất cả" chip alone when no material has a price yet', async () => {
    result = { items: [], total: 0 }
    options = []
    build()
    expect(await screen.findByText('Chưa có nguyên liệu nào có giá.')).toBeInTheDocument()
    await waitFor(() => expect(picker()).toBeEnabled())
    const chips = within(screen.getByRole('group', { name: 'Lọc theo nhóm' })).getAllByRole('button')
    expect(chips.map((chip) => chip.textContent)).toEqual(['Tất cả'])
  })
})
