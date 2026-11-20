// duoc-CR-784 — hộp thoại Báo giá mới. Chặn ở tầng `@/core/api` (luật testing.md) để đếm đúng số lệnh POST.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'

const postCalls: { url: string; body: unknown }[] = []
let resolvePost: (() => void) | null = null

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    //  Treo lệnh POST tới khi bài kiểm thả ra — mô phỏng máy chủ chậm để bấm đúp lọt vào giữa.
    apiPost: (url: string, body: unknown) => {
      postCalls.push({ url, body })
      return new Promise((resolve) => {
        resolvePost = () => resolve({ id: 1 })
      })
    },
  }
})
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

import { PackagingQuoteDialog } from './packaging-quote-dialog'

function renderDialog(props: { defaultCode?: string } = {}) {
  const onOpenChange = vi.fn()
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  render(
    <QueryClientProvider client={client}>
      <PackagingQuoteDialog open onOpenChange={onOpenChange} {...props} />
    </QueryClientProvider>,
  )
  return { onOpenChange, user: userEvent.setup() }
}

beforeEach(() => {
  postCalls.length = 0
  resolvePost = null
})

describe('PackagingQuoteDialog', () => {
  it('blocks saving without a product code and says why', async () => {
    const { user } = renderDialog()
    await user.type(screen.getByLabelText(/Đơn giá/), '1200')
    await user.click(screen.getByRole('button', { name: 'Lưu báo giá' }))
    expect(screen.getByText('Nhập mã vật tư bao bì.')).toBeInTheDocument()
    expect(postCalls).toHaveLength(0)
  })

  it('cannot produce a negative price: the minus sign is dropped and an empty price is blocked', async () => {
    const { user } = renderDialog({ defaultCode: 'NAP0085' })
    await user.type(screen.getByLabelText(/Đơn giá/), '-')
    await user.click(screen.getByRole('button', { name: 'Lưu báo giá' }))
    expect(screen.getByText(/Nhập đơn giá/)).toBeInTheDocument()
    expect(postCalls).toHaveLength(0)
  })

  it('a double click sends exactly one POST with the Vietnamese-formatted price parsed', async () => {
    const { user, onOpenChange } = renderDialog({ defaultCode: 'nap0085' })
    await user.type(screen.getByLabelText(/Đơn giá/), '1.234,5')
    await user.dblClick(screen.getByRole('button', { name: 'Lưu báo giá' }))
    expect(postCalls).toHaveLength(1)
    expect(postCalls[0]).toMatchObject({
      url: '/api/product-price-quotes',
      body: { product_code: 'NAP0085', price: 1234.5 },
    })
    resolvePost?.()
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false))
  })

  it('shows the code as read-only text (no editable box) when opened from a price-list row', () => {
    renderDialog({ defaultCode: 'cpt0105' })
    expect(screen.getByText('CPT0105')).toBeInTheDocument()
    expect(screen.queryByPlaceholderText('Vd: NAP0085')).not.toBeInTheDocument()
  })

  it('every button except the submit is type="button", so it never saves by accident', () => {
    renderDialog()
    const buttons = screen.getAllByRole('button').filter((b) => b.closest('form'))
    const submits = buttons.filter((b) => b.getAttribute('type') === 'submit')
    expect(submits.map((b) => b.textContent)).toEqual(['Lưu báo giá'])
  })
})
