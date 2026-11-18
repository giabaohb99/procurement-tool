import { fireEvent, render, screen } from '@testing-library/react'
import { useState } from 'react'
import { describe, expect, it } from 'vitest'

import { WORK_ROLE, type WorkMember } from '../types/work'
import { WorkCreateGroupMembersPicker } from './work-create-group-members-picker'

function member(employeeId: number, name: string, role: number): WorkMember {
  return {
    id: employeeId,
    employee_id: employeeId,
    role,
    department_id: null,
    employee_name: name,
    employee_code: `NV${employeeId}`,
  }
}

const MEMBERS = [
  member(1, 'Huỳnh Gia Bảo', WORK_ROLE.OWNER),
  member(2, 'Trần An', WORK_ROLE.MEMBER),
  member(3, 'Lê Bình', WORK_ROLE.VIEWER),
]

/** Bọc state thật như hộp tạo dự án, để bấm xong đọc lại được tập người bị bỏ chọn. */
function Harness({ members = MEMBERS }: { members?: WorkMember[] }) {
  const [assign, setAssign] = useState(true)
  const [excluded, setExcluded] = useState<Set<number>>(() => new Set())
  return (
    <>
      <WorkCreateGroupMembersPicker
        members={members}
        isLoading={false}
        assign={assign}
        onAssignChange={setAssign}
        excluded={excluded}
        onExcludedChange={setExcluded}
      />
      <output data-testid="picked">
        {assign ? members.filter((m) => !excluded.has(m.employee_id)).map((m) => m.employee_id).join(',') : 'none'}
      </output>
    </>
  )
}

const picked = () => screen.getByTestId('picked').textContent

describe('WorkCreateGroupMembersPicker (duoc-CR-783)', () => {
  it('starts with assigning turned on and every group member chosen', () => {
    render(<Harness />)
    expect(screen.getByRole('checkbox', { name: 'Gán thành viên của nhóm vào dự án' })).toBeChecked()
    expect(picked()).toBe('1,2,3')
    expect(screen.getByText('3/3 người')).toBeInTheDocument()
  })

  it('lets the creator drop one person and pick everyone again with "select all"', () => {
    render(<Harness />)
    fireEvent.click(screen.getByRole('checkbox', { name: 'Gán Trần An' }))
    expect(picked()).toBe('1,3')
    expect(screen.getByText('2/3 người')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('checkbox', { name: 'Chọn tất cả thành viên nhóm' }))
    expect(picked()).toBe('1,2,3')
    fireEvent.click(screen.getByRole('checkbox', { name: 'Chọn tất cả thành viên nhóm' }))
    expect(picked()).toBe('')
  })

  it('hides the list and sends nobody when assigning is turned off', () => {
    render(<Harness />)
    fireEvent.click(screen.getByRole('checkbox', { name: 'Gán thành viên của nhóm vào dự án' }))
    expect(picked()).toBe('none')
    expect(screen.queryByText('Huỳnh Gia Bảo')).not.toBeInTheDocument()
  })

  it('shows the group owner as admin, because a project keeps exactly one owner', () => {
    render(<Harness members={[member(1, 'Huỳnh Gia Bảo', WORK_ROLE.OWNER)]} />)
    expect(screen.getByText('Quản trị')).toBeInTheDocument()
    expect(screen.queryByText('Chủ sở hữu')).not.toBeInTheDocument()
  })

  it('says so when the group has nobody else to assign', () => {
    render(<Harness members={[]} />)
    expect(screen.getByText('Nhóm chưa có thành viên nào khác ngoài bạn.')).toBeInTheDocument()
  })
})
