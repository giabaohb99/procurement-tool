import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { LeaveBalanceMissingContractStrip } from './leave-balance-missing-contract-strip'

const text = () => document.body.textContent?.replace(/\s+/g, ' ') ?? ''

describe('LeaveBalanceMissingContractStrip (duoc-CR-762 option B)', () => {
  it('renders nothing when nobody is missing a contract', () => {
    const { container } = render(
      <LeaveBalanceMissingContractStrip summary={{ missing: 0, total: 5, showRowBadges: true }} />,
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('<= half missing: plain count, no filter button (row badges already show who)', () => {
    render(
      <LeaveBalanceMissingContractStrip
        summary={{ missing: 2, total: 10, showRowBadges: true }}
        filter={{ active: false, onToggle: vi.fn() }}
      />,
    )
    expect(text()).toContain('2 nhân sự chưa đủ HĐLĐ trên hệ thống — phép năm đang tính từ ngày vào làm.')
    expect(screen.queryByRole('button')).toBeNull()
  })

  it('> half missing: reads N/M and offers the client-side filter, toggling its label', async () => {
    const onToggle = vi.fn()
    const { rerender } = render(
      <LeaveBalanceMissingContractStrip
        summary={{ missing: 262, total: 262, showRowBadges: false }}
        filter={{ active: false, onToggle }}
      />,
    )
    expect(text()).toContain('262/262 người chưa đủ HĐLĐ trên hệ thống — phép năm đang tính từ ngày vào làm')
    await userEvent.click(screen.getByRole('button', { name: 'Chỉ hiện người chưa đủ HĐLĐ' }))
    expect(onToggle).toHaveBeenCalledTimes(1)

    rerender(
      <LeaveBalanceMissingContractStrip
        summary={{ missing: 262, total: 262, showRowBadges: false }}
        filter={{ active: true, onToggle }}
      />,
    )
    expect(screen.getByRole('button', { name: 'Hiện tất cả' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('server-paginated table: scope note, and no button even when above half', () => {
    render(
      <LeaveBalanceMissingContractStrip
        summary={{ missing: 3, total: 4, showRowBadges: false }}
        scopeNote="trên trang đang xem"
      />,
    )
    expect(text()).toContain('3/4 người trên trang đang xem chưa đủ HĐLĐ')
    expect(screen.queryByRole('button')).toBeNull()
  })
})
