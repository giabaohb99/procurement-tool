// duoc-CR-784 — màn Tác động giá: ba thẻ số liệu đầu màn đã BỎ theo người chủ (23/11/2026, bản in vẫn giữ thẻ).
// Bài này canh để thẻ không quay lại và bảng sản phẩm vẫn để máy chủ xếp mặc định theo mã HH.
// Chặn ở tầng `@/core/api` (luật testing.md); ô chọn mã thay bằng một nút vì cách chọn mã đã có bài kiểm riêng.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router-dom'
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
        applied: 1100, diff: 100, pct: 0.1, usage: 2, min: 900, max: 1100,
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
    //  Danh sách mã của ô chọn (`/code-options`): mã lạ trên URL bị bỏ theo danh sách này.
    apiGet: async () => [{ code: 'CPT0105', name: 'Chai 450ml', group: 'Chai', usage: 2, new: 1100 }],
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

/** In chuỗi truy vấn hiện tại để bài kiểm đọc được URL màn vừa ghi. */
function LocationProbe() {
  return <output data-testid="search">{useLocation().search}</output>
}

function build(initialSearch = '') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/procurement/packaging-cost${initialSearch}`]}>
        <PackagingImpactPage />
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  bodies.length = 0
  topProduct = { fg_code: 'HH0417.1', fg_name: 'Nước tương 450ml', diff_bottle: 100, diff_carton: 4000, carton_qty: 40 }
  Element.prototype.scrollIntoView = vi.fn()
})

describe('PackagingImpactPage without summary cards', () => {
  it('does not render the removed cards after a code is chosen', async () => {
    build()
    await userEvent.click(screen.getByRole('button', { name: 'chọn mã giả lập' }))
    await waitFor(() => expect(bodies.length).toBeGreaterThan(0))
    expect(screen.queryByText('Tăng nhiều nhất /thùng')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Tăng nhiều nhất/ })).not.toBeInTheDocument()
    expect(screen.queryByText('Không có sản phẩm tăng')).not.toBeInTheDocument()
  })

  it('lets the server sort products by default (no sort_by in the first POST /impact)', async () => {
    build()
    await userEvent.click(screen.getByRole('button', { name: 'chọn mã giả lập' }))
    await waitFor(() => expect(bodies.length).toBeGreaterThan(0))
    expect(bodies[0]).not.toHaveProperty('sort_by')
  })
})

describe('PackagingImpactPage keeps its selection in the URL', () => {
  it('writes the chosen codes to the URL (replace, no reload needed)', async () => {
    build()
    await userEvent.click(screen.getByRole('button', { name: 'chọn mã giả lập' }))
    await waitFor(() => expect(screen.getByTestId('search')).toHaveTextContent('?codes=CPT0105'))
  })

  it('restores codes, assumed price, keyword, sort and page from the URL on load', async () => {
    build('?codes=CPT0105&assumed=CPT0105:1250&q=abc&sort_by=diff_carton&sort_dir=desc&page=2')
    await waitFor(() => expect(bodies.length).toBeGreaterThan(0))
    expect(bodies[0]).toMatchObject({
      codes: ['CPT0105'],
      assumed_prices: { CPT0105: 1250 },
      q: 'abc',
      sort_by: 'diff_carton',
      sort_dir: 'desc',
      page: 2,
    })
  })

  it('drops a code that is not in the code list once the list has loaded', async () => {
    build('?codes=CPT0105,KHONGCO')
    await waitFor(() =>
      expect(screen.getByTestId('search').textContent).toBe('?codes=CPT0105'),
    )
    expect(bodies.at(-1)).toMatchObject({ codes: ['CPT0105'] })
  })
})
