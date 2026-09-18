import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { UnifiedLeaveRequestTable } from './unified-leave-request-table'
import { LEAVE_STATUS, type LeaveInboxRow, type LeaveRequest } from '../types/leave'

const mockToApproveList: LeaveInboxRow[] = [
  {
    id: 101,
    code: 'NP-00101',
    company_id: 1,
    department_id: 1,
    employee_id: 10,
    employee_name: 'Nguyễn Văn A',
    leave_type_id: 1,
    leave_type_name: 'Phép năm',
    from_date: '2026-09-20',
    to_date: '2026-09-21',
    from_session: 1,
    to_session: 1,
    unit: 1,
    total_days: 2,
    reason: 'Việc gia đình',
    contact_phone: '0901234567',
    contact_address: 'Hà Nội',
    status: LEAVE_STATUS.PENDING,
    status_label: 'Chờ duyệt',
    approval_instance_id: 1001,
    document_id: 0,
    decision_note: '',
    task: {
      id: 501,
      instance_id: 1001,
      node_seq: 1,
      node_name: 'Trưởng phòng duyệt',
      due_at: '2026-09-21T17:00:00',
    },
  },
]

const mockAllRequests: LeaveRequest[] = [
  {
    id: 99,
    code: 'NP-00099',
    company_id: 1,
    department_id: 1,
    employee_id: 11,
    employee_name: 'Trần Thị B',
    leave_type_id: 1,
    leave_type_name: 'Phép năm',
    from_date: '2026-09-10',
    to_date: '2026-09-11',
    from_session: 1,
    to_session: 1,
    unit: 1,
    total_days: 2,
    reason: 'Nghỉ mát',
    contact_phone: '',
    contact_address: '',
    status: LEAVE_STATUS.APPROVED,
    status_label: 'Đã duyệt',
    approval_instance_id: 999,
    document_id: 10,
    decision_note: '',
  },
  {
    id: 101,
    code: 'NP-00101',
    company_id: 1,
    department_id: 1,
    employee_id: 10,
    employee_name: 'Nguyễn Văn A',
    leave_type_id: 1,
    leave_type_name: 'Phép năm',
    from_date: '2026-09-20',
    to_date: '2026-09-21',
    from_session: 1,
    to_session: 1,
    unit: 1,
    total_days: 2,
    reason: 'Việc gia đình',
    contact_phone: '',
    contact_address: '',
    status: LEAVE_STATUS.PENDING,
    status_label: 'Chờ duyệt',
    approval_instance_id: 1001,
    document_id: 0,
    decision_note: '',
  },
  {
    id: 102,
    code: 'NP-00102',
    company_id: 1,
    department_id: 1,
    employee_id: 12,
    employee_name: 'Lê Văn C',
    leave_type_id: 2,
    leave_type_name: 'Nghỉ ốm',
    from_date: '2026-09-22',
    to_date: '2026-09-22',
    from_session: 1,
    to_session: 1,
    unit: 1,
    total_days: 1,
    reason: 'Khám sức khỏe',
    contact_phone: '',
    contact_address: '',
    status: LEAVE_STATUS.PENDING,
    status_label: 'Chờ duyệt',
    approval_instance_id: 1002,
    document_id: 0,
    decision_note: '',
  },
]

vi.mock('../hooks/use-leave', () => ({
  useLeaveTypes: () => ({
    data: {
      items: [
        { id: 1, name: 'Phép năm' },
        { id: 2, name: 'Nghỉ ốm' },
      ],
    },
  }),
  useLeaveToApprove: () => ({
    data: { items: mockToApproveList },
    isLoading: false,
    isError: false,
  }),
  useLeaveHandled: () => ({
    data: { items: [] },
    isLoading: false,
    isError: false,
  }),
  useLeaveRequests: () => ({
    data: { items: mockAllRequests, total: mockAllRequests.length },
    isLoading: false,
    isError: false,
  }),
}))

vi.mock('@/core/auth/use-auth', () => ({
  useAuth: () => ({
    user: { id: 1, full_name: 'Admin', employee_id: 10 },
  }),
}))

function renderComponent(initialRoute = '/hr/leave-requests') {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialRoute]}>
        <UnifiedLeaveRequestTable />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('UnifiedLeaveRequestTable', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('mặc định phạm vi là «Tất cả» trong ô chọn Select', () => {
    renderComponent()
    // Ô select phạm vi hiển thị giá trị mặc định "Tất cả"
    const selects = screen.getAllByRole('combobox')
    // Select đầu tiên là Select Phạm vi
    expect(selects[0]).toHaveTextContent('Tất cả')
  })

  it('gắn nhãn «Cần bạn duyệt» cho đơn đang nằm trong hàng đợi ký của chính người dùng', () => {
    renderComponent()
    // Đơn NP-00101 nằm trong mockToApproveList
    expect(screen.getByText('Cần bạn duyệt')).toBeInTheDocument()
  })

  it('ở phạm vi Tất cả: ưu tiên đơn Chờ duyệt lên đầu bảng', () => {
    renderComponent()
    // Các dòng đơn được hiển thị
    const rows = screen.getAllByRole('row')
    // Hàng 0 là Header row
    // Hàng 1 phải là NP-00101 (chính tôi cần duyệt, pending)
    // Hàng 2 là NP-00102 (pending khác)
    // Hàng 3 là NP-00099 (đã duyệt)
    expect(rows[1]).toHaveTextContent('NP-00101')
    expect(rows[2]).toHaveTextContent('NP-00102')
    expect(rows[3]).toHaveTextContent('NP-00099')
  })

  it('khi URL có ?scope=to-approve thì lọc chỉ hiện đơn cần duyệt', () => {
    renderComponent('/hr/leave-requests?scope=to-approve')
    expect(screen.getByText('NP-00101')).toBeInTheDocument()
    expect(screen.queryByText('NP-00099')).not.toBeInTheDocument()
  })
})
