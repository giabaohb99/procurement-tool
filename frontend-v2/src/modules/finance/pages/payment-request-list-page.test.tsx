import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ListParams } from '@/shared/types/api'
import { PaymentRequestListPage } from './payment-request-list-page'
import type { PaymentRequestSummary } from '../types/payment-request'

//  Chặn ở tầng HOOK dữ liệu (không phải `@/core/api`) — bài kiểm còn phải bắt
//  được BỘ THAM SỐ gửi đi (`po_code` / `source_type` / `payment_method`…), mà
//  tham số đó chỉ hiện nguyên vẹn ở đầu vào của hook.
const listCalls: ListParams[] = []

vi.mock('../hooks/use-payment-requests', () => ({
  usePaymentRequests: (params: ListParams) => {
    listCalls.push(params)
    return { data: { total: rows.length, items: rows }, isLoading: false, isError: false }
  },
}))

vi.mock('@/modules/hr/hooks/use-companies', () => ({
  useCompanies: () => ({ data: { total: 1, items: [{ id: 7, name: 'Công ty Dego Cần Thơ' }] } }),
}))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: () => true,
    canAccess: () => true,
  }),
}))

function paymentRequest(over: Partial<PaymentRequestSummary> & { id: number }): PaymentRequestSummary {
  return {
    code: `YCTT-${over.id}`,
    supplier_code: `NCC-${over.id}`,
    supplier_name: `Nhà cung cấp ${over.id}`,
    company_id: 7,
    source_type: 'goods',
    request_date: '2026-09-01',
    payment_method: 'transfer',
    prepay: 0,
    total: 1000000,
    note: '',
    reject_reason: '',
    status: 'draft',
    misa_code: '',
    created_by_name: 'Người lập',
    ...over,
  } as PaymentRequestSummary
}

const rows: PaymentRequestSummary[] = [paymentRequest({ id: 1 }), paymentRequest({ id: 2 })]

function build(url = '/finance/payment-requests') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <PaymentRequestListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function lastCall() {
  return listCalls[listCalls.length - 1]
}

/**
 * Nút **Bộ lọc** của khổ RỘNG (popover gộp Loại nợ + Hình thức thanh toán).
 *
 * ⚠️ Trang dựng HAI nút cùng tên: một của tờ trượt khổ hẹp (`QuickFilterSheet`,
 * mang `md:hidden`) và một của popover khổ rộng (mang `max-md:hidden`). jsdom
 * không áp CSS nên cả hai cùng nằm trong cây — bản khổ rộng dựng SAU trong
 * JSX nên là nút cuối. Cùng khuôn `survey-report-page.test.tsx` /
 * `payable-list-page.test.tsx`.
 */
async function desktopFilterTrigger() {
  const triggers = await screen.findAllByRole('button', { name: 'Bộ lọc' })
  return triggers[triggers.length - 1]
}

beforeEach(() => {
  listCalls.length = 0
})

/** ai-CR-017: đồng bộ v1 — bù ô "Mã PO" ra thanh lọc ngoài. */
describe('PaymentRequestListPage — ô Mã PO (ai-CR-017)', () => {
  it('sends po_code only after the debounce settles', async () => {
    const user = userEvent.setup()
    build()

    await user.type(screen.getByLabelText('Lọc theo mã ĐMH'), 'PO-9')
    expect(lastCall().po_code).toBeUndefined()

    await vi.waitFor(() => expect(lastCall().po_code).toBe('PO-9'), { timeout: 1000 })
  })

  it('drops the param again once the box is cleared — hacker gõ rồi xóa sạch', async () => {
    const user = userEvent.setup()
    build()

    const input = screen.getByLabelText('Lọc theo mã ĐMH')
    await user.type(input, 'PO-9')
    await vi.waitFor(() => expect(lastCall().po_code).toBe('PO-9'), { timeout: 1000 })

    await user.clear(input)
    await vi.waitFor(() => expect(lastCall().po_code).toBeUndefined(), { timeout: 1000 })
  })
})

/** ai-CR-017: Loại nợ / Hình thức TT dời khỏi thanh lọc ngoài, khớp v1. */
describe('PaymentRequestListPage — Loại nợ / Hình thức TT dời vào Bộ lọc (ai-CR-017)', () => {
  it('không còn bày Loại nợ / Hình thức TT thẳng trên thanh công cụ', () => {
    // Radix Popover không mount nội dung khi đang đóng — hai ô này giờ chỉ
    // xuất hiện sau khi bấm nút "Bộ lọc".
    build()

    expect(screen.queryByRole('combobox', { name: 'Lọc theo loại nợ' })).not.toBeInTheDocument()
    expect(
      screen.queryByRole('combobox', { name: 'Lọc theo hình thức thanh toán' }),
    ).not.toBeInTheDocument()
  })

  it('sends source_type after picking Loại nợ inside the popover', async () => {
    const user = userEvent.setup()
    build()

    await user.click(await desktopFilterTrigger())
    await user.click(screen.getByRole('combobox', { name: 'Lọc theo loại nợ' }))
    await user.click(screen.getByRole('option', { name: 'Vận chuyển' }))

    expect(lastCall().source_type).toBe('shipping')
  })

  it('sends payment_method after picking Hình thức thanh toán inside the popover', async () => {
    const user = userEvent.setup()
    build()

    await user.click(await desktopFilterTrigger())
    await user.click(screen.getByRole('combobox', { name: 'Lọc theo hình thức thanh toán' }))
    await user.click(screen.getByRole('option', { name: 'Tiền mặt' }))

    expect(lastCall().payment_method).toBe('cash')
  })
})
