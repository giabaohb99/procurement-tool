import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { EmployeeDetail } from '../types/employee'
import { EmployeeDetailSidebar } from './employee-detail-sidebar'
import { EmployeeStatusIndicator } from './employee-status-indicator'

function makeEmployee(overrides: Partial<EmployeeDetail> = {}): EmployeeDetail {
  return {
    id: 304,
    code: 'MKT_TP',
    full_name: 'Trưởng phòng thường',
    email: '',
    phone: '',
    company_id: 1,
    company_name: 'CÔNG TY TNHH DEGO HOLDING',
    department_id: 2,
    department_name: 'Hành chính',
    position: 'Nhân viên (Demo)',
    role_name: '',
    status: 'official',
    status_label: 'Chính thức',
    is_active: true,
    gender: 0,
    avatar: '',
    signature: '',
    user_id: 10,
    ...overrides,
  }
}

const TODAY = new Date(2026, 10, 2)

describe('EmployeeDetailSidebar', () => {
  it('says the direct manager is unassigned instead of hiding the row', () => {
    //  «Chưa gán» là thông tin: bộ máy duyệt lùi về trưởng bộ phận.
    render(<EmployeeDetailSidebar employee={makeEmployee()} avatar={null} today={TODAY} />)
    expect(screen.getByText('Quản lý trực tiếp')).toBeInTheDocument()
    expect(screen.getByText('Chưa gán')).toBeInTheDocument()
  })

  it('shows the manager name when assigned', () => {
    render(
      <EmployeeDetailSidebar
        employee={makeEmployee({ direct_manager_name: 'Nguyễn Văn A' })}
        avatar={null}
        today={TODAY}
      />,
    )
    expect(screen.getByText('Nguyễn Văn A')).toBeInTheDocument()
    expect(screen.queryByText('Chưa gán')).not.toBeInTheDocument()
  })

  it('hides identity rows whose value is empty rather than printing blank labels', () => {
    render(
      <EmployeeDetailSidebar
        employee={makeEmployee({ position: '', department_name: null, company_name: '' })}
        avatar={null}
        today={TODAY}
      />,
    )
    expect(screen.queryByText('Chức vụ')).not.toBeInTheDocument()
    expect(screen.queryByText('Phòng ban')).not.toBeInTheDocument()
    expect(screen.queryByText('Công ty')).not.toBeInTheDocument()
    expect(screen.getByText('MKT_TP')).toBeInTheDocument()
  })

  it('shows birthday and work anniversary on the matching day with tenure', () => {
    render(
      <EmployeeDetailSidebar
        employee={makeEmployee({ date_of_birth: '1990-11-02', hire_date: '2023-11-02' })}
        avatar={null}
        today={TODAY}
      />,
    )
    expect(screen.getByText('Sinh nhật hôm nay')).toBeInTheDocument()
    expect(screen.getByText('Tròn 3 năm làm việc')).toBeInTheDocument()
    expect(screen.getByText(/02\/11\/2023/)).toBeInTheDocument()
    expect(screen.getByText(/3 năm/, { selector: 'span' })).toBeInTheDocument()
  })

  it('shows no milestone block at all when hire date is missing and birth date is masked', () => {
    render(
      <EmployeeDetailSidebar
        employee={makeEmployee({ date_of_birth: '', hire_date: null })}
        avatar={null}
        today={TODAY}
      />,
    )
    expect(screen.queryByText('Vào làm')).not.toBeInTheDocument()
    expect(screen.queryByText('Sinh nhật hôm nay')).not.toBeInTheDocument()
  })
})

describe('EmployeeStatusIndicator', () => {
  it('adds a «Ngừng dùng» badge only when the profile is inactive', () => {
    const { rerender } = render(
      <EmployeeStatusIndicator status="resigned" statusLabel="Nghỉ việc" isActive={false} />,
    )
    expect(screen.getByText('Nghỉ việc')).toBeInTheDocument()
    expect(screen.getByText('Ngừng dùng')).toBeInTheDocument()

    rerender(<EmployeeStatusIndicator status="official" statusLabel="Chính thức" isActive />)
    expect(screen.queryByText('Ngừng dùng')).not.toBeInTheDocument()
  })

  it('falls back to the code table when the backend label is empty, and to the raw code when unknown', () => {
    const { rerender } = render(
      <EmployeeStatusIndicator status="maternity_leave" statusLabel="" isActive />,
    )
    expect(screen.getByText('Nghỉ thai sản')).toBeInTheDocument()

    rerender(<EmployeeStatusIndicator status="ma_la" statusLabel="" isActive />)
    expect(screen.getByText('ma_la')).toBeInTheDocument()
  })
})
