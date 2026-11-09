import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { EmployeeChangeRequest } from '../types/employee-change-request'
import { ProfileChangeRequestCard } from './profile-change-request-card'

function request(overrides: Partial<EmployeeChangeRequest> = {}): EmployeeChangeRequest {
  return {
    id: 5,
    employee_id: 7,
    employee_code: 'NSU007',
    employee_name: 'Nguyễn Văn Thử',
    status: 1,
    items: [
      {
        group: 'personal',
        field: 'marital_status',
        before: 1,
        after: 2,
        current: 1,
        masked: false,
      },
      {
        group: 'bank',
        field: 'bank_account_no',
        before: '1',
        after: '2',
        current: '1',
        masked: false,
      },
    ],
    families: null,
    note: '',
    reject_reason: '',
    created_at: '2026-11-03T09:15:00',
    created_by_name: 'Nguyễn Văn Thử',
    decided_at: null,
    decided_by_name: '',
    can_decide: true,
    has_sensitive: false,
    ...overrides,
  }
}

describe('ProfileChangeRequestCard', () => {
  it('bày tên, mã NV, nhóm thay đổi, số trường, ngày gửi và huy hiệu trạng thái', () => {
    render(<ProfileChangeRequestCard request={request()} />)

    expect(screen.getByText('Nguyễn Văn Thử')).toBeInTheDocument()
    expect(screen.getByText('NSU007')).toBeInTheDocument()
    expect(screen.getByText('Cá nhân, Ngân hàng')).toBeInTheDocument()
    expect(screen.getByText('2 trường')).toBeInTheDocument()
    //  Có cả GIỜ như cột Ngày gửi của bảng — hai đề nghị cùng ngày phải phân biệt được. `created_at` của
    //  backend là giờ UTC không kèm múi, hiển thị theo giờ VN: 09:15 UTC thành 16:15.
    expect(screen.getByText(/Gửi 03\/11\/2026 16:15/)).toBeInTheDocument()
    expect(screen.getByText('Chờ duyệt')).toBeInTheDocument()
  })

  it('hộ gia đình tính là MỘT trường và có mặt trong danh sách nhóm', () => {
    render(
      <ProfileChangeRequestCard
        request={request({ items: [], families: { before: [], after: [], masked: false } })}
      />,
    )
    expect(screen.getByText('1 trường')).toBeInTheDocument()
    expect(screen.getByText('Hộ gia đình')).toBeInTheDocument()
  })

  it('tên rỗng thì dòng đầu lấy #id thay vì để trống', () => {
    render(<ProfileChangeRequestCard request={request({ employee_name: '' })} />)
    expect(screen.getByText('#7')).toBeInTheDocument()
  })

  //  Thẻ nằm TRONG một <button> của DataTableMobileCards (bảng có onRowClick) — nút lồng nút là HTML sai.
  it('không chứa nút nào và không dùng thẻ khối bên trong', () => {
    const { container } = render(<ProfileChangeRequestCard request={request()} />)
    expect(screen.queryByRole('button')).toBeNull()
    expect(container.querySelector('div, p')).toBeNull()
  })
})
