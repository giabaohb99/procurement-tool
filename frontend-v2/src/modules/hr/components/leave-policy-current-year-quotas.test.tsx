import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import type { PolicyCurrentYearQuota } from '../types/leave-policy'
import { LeavePolicyCurrentYearQuotas } from './leave-policy-current-year-quotas'

function renderQuotas(quotas: PolicyCurrentYearQuota[] | undefined) {
  return render(
    <MemoryRouter>
      <LeavePolicyCurrentYearQuotas quotas={quotas} />
    </MemoryRouter>,
  )
}

describe('LeavePolicyCurrentYearQuotas', () => {
  it('links each leave type to its leave balance row, with a Vietnamese decimal comma', () => {
    renderQuotas([{ leave_type_id: 1, leave_type_name: 'Phép năm', allocated_days: 13.5, balance_id: 42 }])
    const link = screen.getByRole('link', { name: /Phép năm 13,5 ngày/ })
    expect(link).toHaveAttribute('href', '/hr/leave-balances/42')
  })

  it('says the fund is not granted yet instead of linking to a balance row that does not exist', () => {
    renderQuotas([{ leave_type_id: 2, leave_type_name: 'Nghỉ thêm', allocated_days: null, balance_id: 0 }])
    expect(screen.getByText('Nghỉ thêm: chưa cấp quỹ')).toBeInTheDocument()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })

  it('shows a dash for an assignment that does not touch this year', () => {
    renderQuotas([])
    expect(screen.getByText('—')).toBeInTheDocument()
  })

  it('renders nothing when an old backend did not send the field', () => {
    const { container } = renderQuotas(undefined)
    expect(container).toBeEmptyDOMElement()
  })

  it('shows zero days as a real quota (a 0-day trial policy), not as missing', () => {
    renderQuotas([{ leave_type_id: 1, leave_type_name: 'Phép năm', allocated_days: 0, balance_id: 7 }])
    expect(screen.getByRole('link', { name: /Phép năm 0 ngày/ })).toHaveAttribute('href', '/hr/leave-balances/7')
  })
})
