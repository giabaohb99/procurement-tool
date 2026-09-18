import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type * as ReactRouterModule from 'react-router-dom'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

type ReactRouter = typeof ReactRouterModule

import { LEAVE_SESSION, LEAVE_STATUS, type LeaveRequest } from '../types/leave'
import { LeaveRequestPrintPage } from './leave-request-print-page'

const testRequest = vi.hoisted(() => ({ current: null as LeaveRequest | null }))

vi.mock('../hooks/use-leave', () => ({
  useLeaveRequest: () => ({
    data: testRequest.current,
    isLoading: false,
  }),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<ReactRouter>('react-router-dom')
  return {
    ...actual,
    useParams: () => ({ id: '10' }),
  }
})

function mockRequest(overrides: Partial<LeaveRequest> = {}): LeaveRequest {
  return {
    id: 10,
    code: 'NP-2026-0010',
    company_id: 1,
    department_id: 2,
    department_name: 'Lập trình & IT nội bộ',
    employee_id: 3,
    employee_name: 'Phạm Lê Triết Giang',
    employee_position: 'Chuyên viên',
    leave_type_id: 1,
    leave_type_name: 'Phép năm',
    from_date: '2026-06-09',
    to_date: '2026-06-09',
    from_session: LEAVE_SESSION.FULL,
    to_session: LEAVE_SESSION.FULL,
    unit: 1,
    total_days: 1,
    reason: 'Em xin phép nghỉ 1 ngày để đưa vợ con về Châu Đốc',
    contact_phone: '0973555582',
    contact_address: 'Cần Thơ',
    status: LEAVE_STATUS.APPROVED,
    approval_instance_id: 5,
    document_id: 0,
    decision_note: '',
    decided_by_name: 'Trần Quang Phú',
    decided_at: '2026-06-09T08:00:00',
    handovers: [],
    ...overrides,
  }
}

describe('LeaveRequestPrintPage', () => {
  it('renders complete leave request sheet with correct fields and structure', () => {
    testRequest.current = mockRequest()
    render(
      <MemoryRouter>
        <LeaveRequestPrintPage />
      </MemoryRouter>,
    )

    // Tiêu đề và biểu tượng
    expect(screen.getByText('ĐƠN XIN NGHỈ PHÉP')).toBeInTheDocument()
    expect(screen.getByAltText('DEGO HOLDING')).toBeInTheDocument()

    // Kính gửi
    expect(screen.getByText(/Trưởng phòng\/Bộ phận\/Nhóm:/)).toBeInTheDocument()
    expect(screen.getByText(/Trưởng phòng HCNS/)).toBeInTheDocument()

    // Thông tin nhân sự & chữ ký
    expect(screen.getAllByText(/Phạm Lê Triết Giang/)).toHaveLength(2)
    expect(screen.getByText(/0973555582/)).toBeInTheDocument()
    expect(screen.getAllByText(/Lập trình & IT nội bộ/)).toHaveLength(2)

    // Lý do & thời gian
    expect(
      screen.getByText(/Em xin phép nghỉ 1 ngày để đưa vợ con về Châu Đốc/),
    ).toBeInTheDocument()
    expect(screen.getByText(/thứ ba 09\/06\/2026/)).toBeInTheDocument()

    // Bàn giao công việc mặc định
    expect(
      screen.getByText(/Cá nhân tự sắp xếp công việc\. Team hỗ trợ công việc/),
    ).toBeInTheDocument()

    // Chữ ký 3 cột
    expect(screen.getByText('P.HCNS')).toBeInTheDocument()
    expect(screen.getByText('Trưởng Phòng/Bộ phận')).toBeInTheDocument()
    expect(screen.getByText('Trần Quang Phú')).toBeInTheDocument()
    expect(screen.getByText('Người làm đơn')).toBeInTheDocument()
  })

  it('triggers window.print when clicking In đơn button', async () => {
    const user = userEvent.setup()
    const printSpy = vi.spyOn(window, 'print').mockImplementation(() => {})

    testRequest.current = mockRequest()
    render(
      <MemoryRouter>
        <LeaveRequestPrintPage />
      </MemoryRouter>,
    )

    const printButton = screen.getByRole('button', { name: /In đơn/i })
    await user.click(printButton)
    expect(printSpy).toHaveBeenCalledOnce()

    printSpy.mockRestore()
  })

  it('correctly handles multi-day range formatting', () => {
    testRequest.current = mockRequest({
      from_date: '2026-06-10',
      to_date: '2026-06-12',
      total_days: 3,
    })
    render(
      <MemoryRouter>
        <LeaveRequestPrintPage />
      </MemoryRouter>,
    )

    expect(
      screen.getByText(/3 ngày, từ ngày 10\/06\/2026 đến ngày 12\/06\/2026/),
    ).toBeInTheDocument()
  })
})
