// duoc-CR-784 — màn Tác động giá: ba thẻ số liệu nằm giữa ô chọn mã và bảng mã đã chọn; bấm thẻ "Tăng nhiều nhất /thùng"
// xếp bảng sản phẩm theo chênh /thùng giảm dần (đi tới máy chủ trong thân POST /impact) rồi cuộn tới bảng.
// Chặn ở tầng `@/core/api` (luật testing.md); ô chọn mã thay bằng một nút vì cách chọn mã đã có bài kiểm riêng.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'

import type { PackagingImpactResult } from '../types/packaging-cost-types'
import { PackagingImpactPage } from './packaging-impact-page'

const bodies: Record<string, unknown>[] = []
let topProduct: PackagingImpactResult['kpis']['max_increase_product'] = null

function impactResult(): PackagingImpactResult {
  return {
    selected: [
      {
        code: 'CPT0105', name: 'Chai 450ml', group: 'Chai', unit: 'Cái', old: 1000, new: 1100, assumed: null,
        applied: 1100, diff: 100, pct: 0.1, usage: 2, min: 900, max: 1100, floor: null, ceiling: null,
      },
    ],
    kpis: {
      selected_count: 1, selected_by_group: { Chai: 1 }, assumed_count: 0, affected_products: 2, increased: 2, decreased: 0,
      max_increase_carton: 4000, max_increase_bottle: 100, max_increase_product: topProduct,
    },
    products: [],
    products_total: 2,
  }
}

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    apiGet: async () => [],
    apiPost: async (_url: string, body: Record<string, unknown>) => {
      bodies.push(body)
      return impactResult()
    },
  }
})

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAccess: () => true }),
}))

vi.mock('../components/packaging-code-picker', () => ({
  PackagingCodePicker: ({ onChange }: { onChange: (codes: string[]) => void }) => (
    <button type="button" onClick={() => onChange(['CPT0105'])}>
      chọn mã giả lập
    </button>
  ),
}))

function build() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <PackagingImpactPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  bodies.length = 0
  topProduct = { hh_code: 'HH0417.1', hh_name: 'Nước tương 450ml', diff_bottle: 100, diff_carton: 4000, carton_qty: 40 }
  Element.prototype.scrollIntoView = vi.fn()
})

describe('PackagingImpactPage summary cards', () => {
  it('shows nothing until a code is chosen, then the three cards', async () => {
    build()
    expect(screen.queryByText('Tăng nhiều nhất /thùng')).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'chọn mã giả lập' }))
    expect(await screen.findByText('Tăng nhiều nhất /thùng')).toBeInTheDocument()
    expect(screen.getByText('Mã đã chọn')).toBeInTheDocument()
    expect(screen.getByText('Sản phẩm bị ảnh hưởng')).toBeInTheDocument()
    expect(screen.getByText('+4.000')).toBeInTheDocument()
  })

  it('sorts the products table by per-carton rise (desc) and scrolls to it when the card is clicked', async () => {
    build()
    await userEvent.click(screen.getByRole('button', { name: 'chọn mã giả lập' }))
    await userEvent.click(await screen.findByRole('button', { name: /Tăng nhiều nhất \/thùng/ }))
    await waitFor(() =>
      expect(bodies[bodies.length - 1]).toMatchObject({ sort_by: 'diff_carton', sort_dir: 'desc', page: 1 }),
    )
    expect(bodies[0]).not.toHaveProperty('sort_by')     // chưa bấm thì máy chủ xếp mặc định theo mã HH
    expect(Element.prototype.scrollIntoView).toHaveBeenCalled()
  })

  it('has no clickable card when no product rises', async () => {
    topProduct = null
    build()
    await userEvent.click(screen.getByRole('button', { name: 'chọn mã giả lập' }))
    expect(await screen.findByText('Không có sản phẩm tăng')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Tăng nhiều nhất/ })).not.toBeInTheDocument()
  })
})
