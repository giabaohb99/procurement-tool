import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { PaymentRequestRefreshDialog } from './payment-request-refresh-dialog'
import type { PaymentRefreshLine, PaymentRefreshPlan } from '../types/payment-request'

//  Chặn ở tầng HOOK: hộp thoại chỉ HIỂN THỊ bản xem trước backend đã tính
//  (`service.plan_refresh`) — luật tính số có bài kiểm riêng ở
//  `test/backend/test_yctt_cap_nhat_theo_cong_no.py`.
let plan: PaymentRefreshPlan | undefined
const mutateAsync = vi.fn(() => Promise.resolve({}))

vi.mock('../hooks/use-payment-requests', () => ({
  usePaymentRequestRefreshPreview: () => ({ data: plan, isLoading: false, isError: false }),
  useRefreshPaymentRequestFromPayables: () => ({ mutateAsync, isPending: false }),
}))

function line(over: Partial<PaymentRefreshLine> & { line_id: number }): PaymentRefreshLine {
  return {
    index: over.line_id,
    state: 'changed',
    reason: 'Theo nợ còn lại 1,500,000 đ',
    payable_ids: [over.line_id],
    payable_remaining: 1_500_000,
    offset_amount: 0,
    po_code_old: 'PO-1',
    po_code_new: 'PO-1',
    invoice_no_old: 'HD-1',
    invoice_no_new: 'HD-1',
    invoice_date_old: '2026-09-01',
    invoice_date_new: '2026-09-01',
    amount_old: 1_000_000,
    amount_new: 1_500_000,
    amount_changed: true,
    changed: true,
    ...over,
  }
}

function buildPlan(over: Partial<PaymentRefreshPlan> = {}): PaymentRefreshPlan {
  return {
    request_id: 9,
    code: 'YCTT00009',
    status: 'draft',
    prepay: 0,
    can_apply: true,
    blocked_reason: '',
    old_total: 1_250_000,
    new_total: 1_500_000,
    changed_count: 2,
    out_of_sync: true,
    lines: [
      line({ line_id: 1 }),
      line({
        line_id: 2,
        state: 'paid_off',
        reason: 'Khoản công nợ đã tất toán — số đề nghị về 0, cân nhắc bỏ dòng',
        amount_old: 250_000,
        amount_new: 0,
      }),
      line({
        line_id: 3,
        state: 'manual',
        reason: 'Không gắn công nợ, giữ nguyên',
        amount_old: 0,
        amount_new: 0,
        amount_changed: false,
        changed: false,
      }),
    ],
    ...over,
  }
}

function renderDialog(canWrite = true) {
  return render(
    <PaymentRequestRefreshDialog open onOpenChange={() => undefined} paymentRequestId={9} canWrite={canWrite} />,
  )
}

describe('PaymentRequestRefreshDialog', () => {
  beforeEach(() => {
    plan = buildPlan()
    mutateAsync.mockClear()
  })

  it('shows every line reason, including hand-typed and paid-off lines, plus the total change', () => {
    renderDialog()
    expect(screen.getByText('Không gắn công nợ, giữ nguyên')).toBeInTheDocument()
    expect(screen.getByText(/đã tất toán/)).toBeInTheDocument()
    expect(screen.getByText(/Tổng đề nghị thanh toán/)).toBeInTheDocument()
  })

  it('applies without sending any client-side numbers', async () => {
    renderDialog()
    await userEvent.click(screen.getByRole('button', { name: /Cập nhật$/ }))
    expect(mutateAsync).toHaveBeenCalledTimes(1)
    expect(mutateAsync).toHaveBeenCalledWith()
  })

  it('disables apply when nothing changed', () => {
    plan = buildPlan({ changed_count: 0 })
    renderDialog()
    expect(screen.getByRole('button', { name: /Cập nhật$/ })).toBeDisabled()
    expect(screen.getByText(/đã khớp công nợ hiện tại/)).toBeInTheDocument()
  })

  it('is read-only for a locked request and says why', () => {
    plan = buildPlan({ status: 'submitted', can_apply: false, blocked_reason: 'Chỉ phiếu Nháp mới cập nhật theo công nợ được' })
    renderDialog()
    expect(screen.queryByRole('button', { name: /Cập nhật$/ })).not.toBeInTheDocument()
    expect(screen.getByText('Chỉ phiếu Nháp mới cập nhật theo công nợ được')).toBeInTheDocument()
  })

  it('hides apply for a user without write permission even on a draft', () => {
    renderDialog(false)
    expect(screen.queryByRole('button', { name: /Cập nhật$/ })).not.toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Đóng' }).length).toBeGreaterThan(0)
  })
})
