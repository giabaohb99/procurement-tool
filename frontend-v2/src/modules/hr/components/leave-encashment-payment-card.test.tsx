import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { EncashmentPayment } from '../types/leave-encashment'
import { LeaveEncashmentPaymentCard } from './leave-encashment-payment-card'

const { granted } = vi.hoisted(() => ({ granted: new Set<string>() }))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string, action = 'read') => granted.has(`${entity}.${action}`) }),
}))

function payment(overrides: Partial<EncashmentPayment> = {}): EncashmentPayment {
  return { id: 41, code: 'YCTT00041', status: 'draft', status_label: 'Nháp', total: null, ...overrides }
}

function renderCard(p: EncashmentPayment | null, cancelBlockedReason = '') {
  return render(
    <MemoryRouter>
      <LeaveEncashmentPaymentCard payment={p} cancelBlockedReason={cancelBlockedReason} />
    </MemoryRouter>,
  )
}

describe('LeaveEncashmentPaymentCard (duoc-CR-719)', () => {
  beforeEach(() => granted.clear())

  it('never shows an amount when the API withholds total (HR approver without payment access)', () => {
    //  Rủi ro chính của phase 04: người duyệt Nhân sự không được thấy tiền (lương ngày x số ngày). Backend gửi
    //  `total: null`; màn hình không được tự vẽ 0 hay một con số nào.
    renderCard(payment({ total: null, status: 'paid', status_label: 'Đã chi' }))
    expect(screen.queryByText('Số tiền')).not.toBeInTheDocument()
    expect(screen.getByText('Đã chi')).toBeInTheDocument()
  })

  it('shows the amount only when the API sends it, and says accounting has not entered it at 0', () => {
    const { unmount } = renderCard(payment({ total: 0 }))
    expect(screen.getByText('Số tiền')).toBeInTheDocument()
    expect(screen.getByText('Kế toán chưa nhập')).toBeInTheDocument()
    unmount()

    renderCard(payment({ total: 2_500_000, status: 'approved', status_label: 'Đã duyệt' }))
    expect(screen.queryByText('Kế toán chưa nhập')).not.toBeInTheDocument()
    expect(screen.getByText(/2\.500\.000/)).toBeInTheDocument()
  })

  it('links the payment request code only for users who can read payment requests', () => {
    const { unmount } = renderCard(payment())
    expect(screen.getByText('YCTT00041')).toBeInTheDocument()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
    unmount()

    granted.add('payment_request.read')
    renderCard(payment())
    expect(screen.getByRole('link', { name: /YCTT00041/ })).toHaveAttribute('href', '/finance/payment-requests/41')
  })

  it('explains why cancel is blocked, and stays quiet when the reason is blank', () => {
    const { unmount } = renderCard(payment(), '   ')
    expect(screen.queryByText(/Chưa hủy được phiếu/)).not.toBeInTheDocument()
    unmount()

    renderCard(payment({ status: 'submitted' }), 'YCTT YCTT00041 đang ở Chờ duyệt — kế toán từ chối YCTT trước')
    expect(screen.getByText(/Chưa hủy được phiếu: YCTT YCTT00041 đang ở Chờ duyệt/)).toBeInTheDocument()
  })

  it('says there is no payment request yet when the block is null', () => {
    renderCard(null)
    expect(screen.getByText('Chưa có yêu cầu thanh toán cho phiếu này.')).toBeInTheDocument()
  })
})
