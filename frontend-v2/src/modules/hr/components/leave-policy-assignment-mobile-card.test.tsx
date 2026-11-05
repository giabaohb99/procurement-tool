import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { LEAVE_POLICY_ASSIGNMENT_STATE, type LeavePolicyAssignment } from '../types/leave-policy'
import { LeavePolicyAssignmentMobileCard } from './leave-policy-assignment-mobile-card'

const assignment: LeavePolicyAssignment = {
  id: 7,
  company_id: 1,
  employee_id: 42,
  employee_name: 'Trần Thị Lan',
  employee_code: 'NSU042',
  policy_id: 3,
  policy_name: 'Chính sách khối văn phòng',
  effective_from: '2026-01-01',
  effective_to: null,
  state: LEAVE_POLICY_ASSIGNMENT_STATE.ACTIVE,
  note: '',
}

describe('LeavePolicyAssignmentMobileCard', () => {
  it('shows the policy name by default', () => {
    render(<LeavePolicyAssignmentMobileCard assignment={assignment} />)

    expect(screen.getByText('Trần Thị Lan')).toBeInTheDocument()
    expect(screen.getByText('Chính sách khối văn phòng')).toBeInTheDocument()
  })

  it('drops the policy line inside the policy detail page, where the title already names it', () => {
    render(<LeavePolicyAssignmentMobileCard assignment={assignment} showPolicy={false} />)

    expect(screen.getByText('Trần Thị Lan')).toBeInTheDocument()
    expect(screen.queryByText('Chính sách khối văn phòng')).not.toBeInTheDocument()
  })
})
