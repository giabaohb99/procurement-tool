import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { LeaveBalance } from '../types/leave'
import { LeaveBalanceCard } from './leave-balance-card'

function balance(overrides: Partial<LeaveBalance> = {}): LeaveBalance {
  return {
    id: 1,
    company_id: 1,
    employee_id: 3,
    employee_name: 'Lê Thị C',
    leave_type_id: 4,
    leave_type_name: 'Nghỉ bù',
    year: 2026,
    allocated_days: 0,
    seniority_days: 0,
    carried_days: 0,
    carried_out_days: 0,
    carried_expired_days: 0,
    adjusted_days: 0,
    used_days: 0,
    pending_days: 0,
    total_days: 0,
    remaining_days: 0,
    note: '',
    ...overrides,
  }
}

describe('LeaveBalanceCard comp_days', () => {
  it('shows the compensatory days as an extra and paints a spent comp-only row red like other quota rows', () => {
    const { container } = render(
      <LeaveBalanceCard balance={balance({ comp_days: 1.5, total_days: 1.5, used_days: 1.5 })} />,
    )
    expect(screen.getByText(/\+1\.5 nghỉ bù/)).toBeInTheDocument()
    expect(container.querySelector('.text-lg')?.className).toContain('text-destructive')
  })

  it('keeps a no-quota row muted and prints no comp extra when comp_days is 0 or missing', () => {
    const { container } = render(<LeaveBalanceCard balance={balance()} />)
    expect(screen.queryByText(/nghỉ bù$/)).not.toBeInTheDocument()
    expect(container.querySelector('.text-lg')?.className).toContain('text-muted-foreground')
  })
})

describe('LeaveBalanceCard encashed_days (duoc-CR-719)', () => {
  it('prints the encashed days as a deduction, without a plus sign', () => {
    render(<LeaveBalanceCard balance={balance({ allocated_days: 12, total_days: 12, encashed_days: 4, remaining_days: 8 })} />)
    expect(screen.getByText(/4 đã thanh toán/)).toBeInTheDocument()
    expect(screen.queryByText(/\+4 đã thanh toán/)).not.toBeInTheDocument()
  })

  it('prints nothing about encashment when encashed_days is 0 or missing', () => {
    render(<LeaveBalanceCard balance={balance({ encashed_days: 0 })} />)
    expect(screen.queryByText(/đã thanh toán/)).not.toBeInTheDocument()
  })
})
