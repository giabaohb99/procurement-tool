import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { PaymentRequest } from '../types/payment-request'
import { PaymentRequestLeaveEncashmentView } from './payment-request-leave-encashment-view'

const { updateMutateAsync, actionMutateAsync, granted } = vi.hoisted(() => ({
  updateMutateAsync: vi.fn(),
  actionMutateAsync: vi.fn(),
  granted: new Set<string>(),
}))

vi.mock('../hooks/use-payment-requests', () => ({
  useUpdatePaymentRequest: () => ({ mutateAsync: updateMutateAsync, isPending: false }),
  usePaymentRequestAction: () => ({ mutateAsync: actionMutateAsync, mutate: vi.fn(), isPending: false }),
}))
vi.mock('@/modules/hr/hooks/use-companies', () => ({
  useCompanies: () => ({ data: { total: 1, items: [{ id: 7, name: 'Công ty Dego Cần Thơ' }] } }),
}))
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string, action = 'read') => granted.has(`${entity}.${action}`) }),
}))
//  Hai thẻ dùng chung tự gọi API — không phải thứ bài này kiểm.
vi.mock('@/modules/procurement/components/document-attachments-card', () => ({ DocumentAttachmentsCard: () => null }))
vi.mock('@/shared/audit', () => ({ AuditTimeline: () => null }))

function payout(overrides: Partial<PaymentRequest> = {}): PaymentRequest {
  return {
    id: 41,
    code: 'YCTT00041',
    supplier_code: '',
    supplier_name: 'Nguyễn Văn An (NSU005)',
    company_id: 7,
    source_type: 'leave_encashment',
    request_date: '2026-11-03',
    payment_method: 'transfer',
    prepay: 0,
    total: 0,
    note: 'Thanh toán 2.5 ngày Phép năm năm 2026 — phiếu TTP00009',
    reject_reason: '',
    status: 'draft',
    misa_code: '',
    created_by_name: '',
    payee_employee_id: 5,
    source_ref_id: 9,
    created_at: '2026-11-03T08:00:00',
    print_texts: {},
    lines: [
      {
        id: 77,
        payable_id: 0,
        po_code: 'TTP00009',
        misa_code: '',
        invoice_no: '',
        invoice_date: '',
        amount: 0,
        due_date: '',
        incur_date: '',
        payable_total: 0,
        payable_paid: 0,
        matched: false,
        allocated_amount: 0,
        refunded_amount: 0,
        offset_amount: 0,
        hanging: 0,
      },
    ],
    leave_encashment: {
      id: 9,
      code: 'TTP00009',
      days: 2.5,
      leave_type_name: 'Phép năm',
      balance_year: 2026,
      reason_kind: 1,
    },
    ...overrides,
  }
}

function renderView(req: PaymentRequest) {
  return render(
    <MemoryRouter>
      <PaymentRequestLeaveEncashmentView req={req} />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  granted.clear()
  updateMutateAsync.mockReset().mockResolvedValue({})
  actionMutateAsync.mockReset().mockResolvedValue({})
})

describe('PaymentRequestLeaveEncashmentView', () => {
  it('shows the employee payee, the source label and the leave content, never a supplier', () => {
    granted.add('payment_request.write')
    renderView(payout())
    expect(screen.getByText('Nguyễn Văn An (NSU005)')).toBeInTheDocument()
    expect(screen.getByText('Thanh toán nghỉ phép')).toBeInTheDocument()
    expect(screen.getByText(/2,5 ngày Phép năm năm 2026 · Phép dư cuối năm/)).toBeInTheDocument()
    expect(screen.queryByText('Nhà cung cấp')).not.toBeInTheDocument()
  })

  it('never offers delete, refresh-from-payables, refund or add-line, whatever the permissions', () => {
    for (const p of ['write', 'delete', 'approve', 'print', 'read']) granted.add(`payment_request.${p}`)
    for (const status of ['draft', 'paid'] as const) {
      const { unmount } = renderView(payout({ status }))
      expect(screen.queryByRole('button', { name: /Xóa/ })).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /Cập nhật theo công nợ/ })).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /hoàn tiền/i })).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /Thêm dòng/ })).not.toBeInTheDocument()
      unmount()
    }
  })

  it('blocks "Gửi duyệt" while the amount is 0 and says why', () => {
    granted.add('payment_request.write')
    renderView(payout())
    expect(screen.getByRole('button', { name: /Gửi duyệt/ })).toBeDisabled()
    expect(screen.getByText(/nhập số tiền rồi mới gửi duyệt được/)).toBeInTheDocument()
  })

  it('saves the single line with the typed amount, then submits — once on a double click', async () => {
    granted.add('payment_request.write')
    const user = userEvent.setup()
    let release: () => void = () => {}
    updateMutateAsync.mockImplementation(() => new Promise((resolve) => (release = () => resolve({}))))
    renderView(payout())

    await user.type(screen.getByLabelText('Số tiền thanh toán'), '3500000')
    const submit = screen.getByRole('button', { name: /Gửi duyệt/ })
    expect(submit).toBeEnabled()
    await user.dblClick(submit)
    release()

    await waitFor(() => expect(actionMutateAsync).toHaveBeenCalledWith({ action: 'submit' }))
    expect(updateMutateAsync).toHaveBeenCalledTimes(1)
    expect(actionMutateAsync).toHaveBeenCalledTimes(1)
    expect(updateMutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({
        payment_method: 'transfer',
        lines: [expect.objectContaining({ payable_id: 0, po_code: 'TTP00009', amount: 3500000, offset_amount: 0 })],
      }),
    )
  })

  it('locks the amount once the request left draft, or when the user cannot write', () => {
    granted.add('payment_request.write')
    const { unmount } = renderView(payout({ status: 'submitted', total: 3500000 }))
    expect(screen.queryByLabelText('Số tiền thanh toán')).toBeNull()
    expect(screen.queryByRole('textbox', { name: 'Số tiền thanh toán' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Lưu$/ })).not.toBeInTheDocument()
    unmount()

    granted.clear()
    renderView(payout())
    expect(screen.queryByRole('textbox', { name: 'Số tiền thanh toán' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Gửi duyệt/ })).not.toBeInTheDocument()
  })

  it('links the source encashment only for users who can read it (D1a)', () => {
    renderView(payout())
    expect(screen.getByText('TTP00009')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /TTP00009/ })).not.toBeInTheDocument()
  })

  it('links the source encashment when leave_encashment.read is granted', () => {
    granted.add('leave_encashment.read')
    renderView(payout())
    expect(screen.getByRole('link', { name: /TTP00009/ })).toHaveAttribute('href', '/hr/leave-encashments/9')
  })

  it('shows the status buttons by the usual permission rules (approve on submitted, pay on approved)', () => {
    granted.add('payment_request.approve')
    granted.add('payment_request.write')
    const { unmount } = renderView(payout({ status: 'submitted', total: 1 }))
    expect(screen.getByRole('button', { name: /^Duyệt$/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Từ chối/ })).toBeInTheDocument()
    unmount()
    renderView(payout({ status: 'approved', total: 1 }))
    expect(screen.getByRole('button', { name: /Ghi nhận đã chi/ })).toBeInTheDocument()
  })
})
