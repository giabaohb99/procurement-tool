import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ListParams } from '@/shared/types/api'
import { LeaveCompRequestListPage } from './leave-comp-request-list-page'
import { LeaveEncashmentListPage } from './leave-encashment-list-page'
import type { LeaveCompRequest } from '../types/leave-comp'
import type { LeaveEncashment } from '../types/leave-encashment'

/**
 * duoc-CR-744 — bấm tiêu đề cột Phiếu nghỉ bù và Thanh toán nghỉ phép.
 * - Hai phạm vi có phân trang (Của tôi / Tất cả): gửi `sort_by`/`sort_dir` lên server.
 * - Hàng đợi "Cần tôi duyệt" tải TRỌN (không phân trang, endpoint không nhận sort): xếp tại chỗ theo giá trị
 *   ô đang hiện, ô trống luôn xuống cuối ở cả hai chiều.
 */
const compCalls: ListParams[] = []
const encashCalls: ListParams[] = []
let compToApprove: LeaveCompRequest[] = []
let encashToApprove: LeaveEncashment[] = []

vi.mock('../hooks/use-leave-comp', () => ({
  useLeaveCompRequests: (params: ListParams) => {
    compCalls.push(params)
    return { data: { total: 0, items: [] }, isLoading: false, isError: false }
  },
  useLeaveCompToApprove: () => ({ data: { total: compToApprove.length, items: compToApprove } }),
}))
vi.mock('../hooks/use-leave-encashment', () => ({
  useLeaveEncashments: (params: ListParams) => {
    encashCalls.push(params)
    return { data: { total: 0, items: [] }, isLoading: false, isError: false }
  },
  useLeaveEncashmentToApprove: () => ({ data: { total: encashToApprove.length, items: encashToApprove } }),
}))
vi.mock('@/core/auth/use-auth', () => ({ useAuth: () => ({ user: { id: 1, employee_id: 5 } }) }))
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAccess: () => true }),
}))

function build(element: React.ReactElement, url: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>{element}</MemoryRouter>
    </QueryClientProvider>,
  )
}

const header = (text: string) => screen.getByText(text, { selector: 'thead span' })

/** Số phiếu theo thứ tự các dòng đang hiện trong thân bảng. */
function bodyCodes(): string[] {
  const rows = screen.getAllByRole('row').slice(1)
  return rows.map((row) => within(row).getAllByRole('cell')[0].textContent ?? '')
}

function comp(over: Partial<LeaveCompRequest> & { id: number }): LeaveCompRequest {
  return {
    code: `NB${over.id}`,
    company_id: 1,
    department_id: 1,
    department_name: '',
    employee_id: 1,
    employee_name: 'An',
    employee_code: '',
    work_date: '2026-03-01',
    days: 1,
    reason: '',
    status: 2,
    status_label: 'Chờ duyệt',
    approval_instance_id: 0,
    decided_at: null,
    decision_note: '',
    created_by: 1,
    created_at: '2026-03-02T00:00:00',
    updated_at: '2026-03-02T00:00:00',
    ...over,
  } as LeaveCompRequest
}

function encash(over: Partial<LeaveEncashment> & { id: number }): LeaveEncashment {
  return {
    code: `TT${over.id}`,
    company_id: 1,
    department_id: 1,
    department_name: '',
    employee_id: 1,
    employee_name: 'An',
    employee_code: '',
    leave_type_id: 1,
    leave_type_name: 'Phép năm',
    balance_year: 2026,
    reason_kind: 1,
    reason_kind_label: 'Phép dư cuối năm',
    encashment_date: null,
    days: 1,
    balance_snapshot: 0,
    encashable_snapshot: 0,
    note: '',
    status: 2,
    status_label: 'Chờ duyệt',
    approval_instance_id: 0,
    decided_at: null,
    decision_note: '',
    payment_request_id: 0,
    payment_status: '',
    payment_status_label: '',
    created_by: 1,
    created_at: '2026-03-02T00:00:00',
    updated_at: '2026-03-02T00:00:00',
    ...over,
  } as LeaveEncashment
}

beforeEach(() => {
  compCalls.length = 0
  encashCalls.length = 0
  compToApprove = []
  encashToApprove = []
})

describe('LeaveCompRequestListPage — sắp xếp cột (duoc-CR-744)', () => {
  it('sends sort_by (employee column uses employee_name) and cycles asc -> desc -> off', async () => {
    const user = userEvent.setup()
    build(<LeaveCompRequestListPage />, '/hr/leave-comp-requests?scope=all')
    const last = () => compCalls[compCalls.length - 1]

    const cases: [string, string][] = [
      ['Số phiếu', 'code'],
      ['Người nghỉ', 'employee_name'],
      ['Ngày đi làm', 'work_date'],
      ['Số ngày', 'days'],
      ['Trạng thái', 'status'],
      ['Ngày tạo', 'created_at'],
    ]
    for (const [text, key] of cases) {
      await user.click(header(text))
      expect(last().sort_by, text).toBe(key)
    }

    await user.click(header('Số phiếu'))
    expect(last()).toMatchObject({ sort_by: 'code', sort_dir: 'asc', page: 1 })
    await user.click(header('Số phiếu'))
    expect(last()).toMatchObject({ sort_by: 'code', sort_dir: 'desc' })
    await user.click(header('Số phiếu'))
    expect(last().sort_by).toBeUndefined()
    expect(last().sort_dir).toBeUndefined()
  })

  it('sorts the "Cần tôi duyệt" queue in place: by name, blanks last in BOTH directions', async () => {
    const user = userEvent.setup()
    compToApprove = [
      comp({ id: 1, employee_name: 'Chi' }),
      comp({ id: 2, employee_name: '' }),
      comp({ id: 3, employee_name: 'An' }),
      comp({ id: 4, employee_name: 'Bình' }),
    ]
    build(<LeaveCompRequestListPage />, '/hr/leave-comp-requests?scope=to-approve')

    await user.click(header('Người nghỉ'))
    //  Ô "Người nghỉ" hiện `#<id>` khi thiếu tên nhưng giá trị xếp là TÊN rỗng -> xuống cuối.
    expect(bodyCodes()).toEqual(['NB3', 'NB4', 'NB1', 'NB2'])
    await user.click(header('Người nghỉ'))
    expect(bodyCodes()).toEqual(['NB1', 'NB4', 'NB3', 'NB2'])
    await user.click(header('Người nghỉ'))
    //  Thôi sắp xếp: về thứ tự backend trả.
    expect(bodyCodes()).toEqual(['NB1', 'NB2', 'NB3', 'NB4'])
  })

  it('sorts the queue by days numerically and keeps id desc as the tie-break', async () => {
    const user = userEvent.setup()
    compToApprove = [
      comp({ id: 1, days: 1 }),
      comp({ id: 2, days: 0.5 }),
      comp({ id: 3, days: 1 }),
      comp({ id: 4, days: 0.5 }),
    ]
    build(<LeaveCompRequestListPage />, '/hr/leave-comp-requests?scope=to-approve')

    await user.click(header('Số ngày'))   // sortDescFirst: nhịp đầu = giảm dần
    expect(bodyCodes()).toEqual(['NB3', 'NB1', 'NB4', 'NB2'])
    await user.click(header('Số ngày'))
    expect(bodyCodes()).toEqual(['NB4', 'NB2', 'NB3', 'NB1'])
  })
})

describe('LeaveEncashmentListPage — sắp xếp cột (duoc-CR-744)', () => {
  it('sends sort_by for every sortable data column', async () => {
    const user = userEvent.setup()
    build(<LeaveEncashmentListPage />, '/hr/leave-encashments?scope=all')
    const last = () => encashCalls[encashCalls.length - 1]

    const cases: [string, string][] = [
      ['Số phiếu', 'code'],
      ['Người được thanh toán', 'employee_name'],
      ['Loại nghỉ', 'leave_type_name'],
      ['Năm quỹ', 'balance_year'],
      ['Lý do', 'reason_kind'],
      ['Số ngày', 'days'],
      ['Trạng thái', 'status'],
      ['Trạng thái chi', 'payment_status'],
      ['Ngày tạo', 'created_at'],
    ]
    for (const [text, key] of cases) {
      await user.click(header(text))
      expect(last().sort_by, text).toBe(key)
    }
  })

  it('sorts the queue by payout status rank (lifecycle, not the alphabet), no payout last in BOTH directions', async () => {
    const user = userEvent.setup()
    encashToApprove = [
      encash({ id: 1, payment_status: 'paid', payment_status_label: 'Đã chi' }),
      encash({ id: 2, payment_status: '' }),
      encash({ id: 3, payment_status: 'draft', payment_status_label: 'Nháp' }),
      encash({ id: 4, payment_status: 'cancelled', payment_status_label: 'Đã từ chối' }),
    ]
    build(<LeaveEncashmentListPage />, '/hr/leave-encashments?scope=to-approve')

    await user.click(header('Trạng thái chi'))
    //  draft < paid < cancelled theo vòng đời; chữ cái của mã sẽ ra cancelled < draft < paid.
    expect(bodyCodes()).toEqual(['TT3', 'TT1', 'TT4', 'TT2'])
    await user.click(header('Trạng thái chi'))
    expect(bodyCodes()).toEqual(['TT4', 'TT1', 'TT3', 'TT2'])
  })

  it('sorts the queue by leave type name and by number of days', async () => {
    const user = userEvent.setup()
    encashToApprove = [
      encash({ id: 1, leave_type_name: 'Phép năm', days: 2 }),
      encash({ id: 2, leave_type_name: 'Bù', days: 10 }),
      encash({ id: 3, leave_type_name: '', days: 1.5 }),
    ]
    build(<LeaveEncashmentListPage />, '/hr/leave-encashments?scope=to-approve')

    await user.click(header('Loại nghỉ'))
    expect(bodyCodes()).toEqual(['TT2', 'TT1', 'TT3'])
    await user.click(header('Số ngày'))   // 10 > 2 > 1.5 theo SỐ, không theo chuỗi ('10' < '2')
    expect(bodyCodes()).toEqual(['TT2', 'TT1', 'TT3'])
    await user.click(header('Số ngày'))
    expect(bodyCodes()).toEqual(['TT3', 'TT1', 'TT2'])
  })
})
