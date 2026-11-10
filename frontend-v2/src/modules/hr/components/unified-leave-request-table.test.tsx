import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { LeaveInboxRow, LeaveRequest } from '../types/leave'
import { UnifiedLeaveRequestTable } from './unified-leave-request-table'

//  duoc-CR-744: chặn ở tầng hook dữ liệu để bắt BỘ THAM SỐ gửi đi khi bấm tiêu đề cột, và để kiểm
//  thứ tự dòng bảng đúng là thứ tự máy chủ trả về (không bị xếp lại trong từng trang).
const requestCalls: Array<Record<string, unknown>> = []

function leave(over: Partial<LeaveRequest> & { id: number }): LeaveRequest {
  return {
    code: `NP-${over.id}`,
    employee_id: over.id,
    employee_name: `Nhân viên ${over.id}`,
    leave_type_id: 1,
    leave_type_name: 'Phép năm',
    from_date: '2026-09-01',
    to_date: '2026-09-02',
    from_session: 1,
    to_session: 1,
    unit: 1,
    total_days: 1,
    reason: '',
    contact_phone: '',
    contact_address: '',
    status: 2,
    approval_instance_id: 0,
    document_id: 0,
    ...over,
  } as LeaveRequest
}

//  Thứ tự máy chủ: đơn "của tôi cần duyệt" (id 5) cố ý đứng CUỐI. Nếu trình duyệt xếp lại thì nó
//  nổi lên đầu bảng - chính là hành vi cũ đã bỏ.
let serverRows: LeaveRequest[] = []
let inboxRows: LeaveInboxRow[] = []

vi.mock('../hooks/use-leave', () => ({
  useLeaveRequests: (params: Record<string, unknown>) => {
    requestCalls.push(params)
    return { data: { total: serverRows.length, items: serverRows }, isLoading: false, isError: false }
  },
  useLeaveToApprove: () => ({ data: { total: inboxRows.length, items: inboxRows }, isLoading: false, isError: false }),
  useLeaveHandled: () => ({ data: { total: 0, items: [] }, isLoading: false, isError: false }),
  useLeaveTypes: () => ({ data: { total: 0, items: [] } }),
}))

vi.mock('@/core/auth/use-auth', () => ({
  useAuth: () => ({ user: { employee_id: 77 } }),
}))

function renderTable(url = '/hr/leave-requests') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <UnifiedLeaveRequestTable />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function lastCall() {
  return requestCalls[requestCalls.length - 1]
}

function header(text: string) {
  return screen.getByText(text, { selector: 'thead span' })
}

/** Số đơn theo thứ tự hàng trong bảng (cột "Số đơn" luôn ghim đầu). */
function renderedCodes() {
  const body = document.querySelector('tbody') as HTMLElement
  return within(body)
    .getAllByText(/^NP-\d+$/)
    .map((el) => el.textContent)
}

beforeEach(() => {
  requestCalls.length = 0
  serverRows = [leave({ id: 9 }), leave({ id: 7 }), leave({ id: 5 })]
  inboxRows = []
})

describe('UnifiedLeaveRequestTable - sắp xếp cột (duoc-CR-744)', () => {
  it('asks the server for mine_first while no column is chosen (scope Tất cả)', () => {
    renderTable()
    expect(lastCall().mine_first).toBe(true)
    expect(lastCall().sort_by).toBeUndefined()
  })

  it('keeps the server order instead of re-sorting the page in the browser', () => {
    inboxRows = [{ ...leave({ id: 5 }), task: { id: 1 } } as unknown as LeaveInboxRow]
    renderTable()
    //  Đơn id 5 là việc của tôi nhưng máy chủ xếp nó cuối trang -> bảng giữ nguyên, không đảo lên đầu.
    expect(renderedCodes()).toEqual(['NP-9', 'NP-7', 'NP-5'])
  })

  it('sends sort_by to the server for each sortable header and drops mine_first', async () => {
    const user = userEvent.setup()
    renderTable()

    const cases: [string, string][] = [
      ['Số đơn', 'code'],
      ['Trạng thái', 'status'],
      ['Người nghỉ', 'employee_name'],
      ['Loại nghỉ', 'leave_type_name'],
      ['Từ ngày', 'from_date'],
      ['Đến ngày', 'to_date'],
      ['Số ngày', 'total_days'],
      ['Lý do', 'reason'],
    ]
    for (const [text, key] of cases) {
      await user.click(header(text))
      expect(lastCall().sort_by, text).toBe(key)
      expect(lastCall().sort_dir, text).toBe('asc')
      expect(lastCall().mine_first, text).toBeUndefined()
    }
  })

  it('cycles asc -> desc -> off and asks for mine_first again once the sort is off', async () => {
    const user = userEvent.setup()
    renderTable()

    await user.click(header('Từ ngày'))
    await user.click(header('Từ ngày'))
    expect(lastCall()).toMatchObject({ sort_by: 'from_date', sort_dir: 'desc' })
    await user.click(header('Từ ngày'))
    expect(lastCall().sort_by).toBeUndefined()
    expect(lastCall().mine_first).toBe(true)
  })

  it('goes back to page 1 when the sort changes', async () => {
    const user = userEvent.setup()
    renderTable()
    await user.click(header('Người nghỉ'))
    expect(lastCall().page).toBe(1)
  })

  it('does not ask for mine_first in the "Đơn của tôi" scope but still sorts on the server', async () => {
    const user = userEvent.setup()
    renderTable('/hr/leave-requests?scope=mine')
    expect(lastCall().mine_first).toBeUndefined()
    expect(lastCall().employee_id).toBe('77')
    await user.click(header('Từ ngày'))
    expect(lastCall()).toMatchObject({ sort_by: 'from_date', employee_id: '77' })
  })

  it('sorts the loaded inbox in the browser across the whole list (scope Cần tôi duyệt)', async () => {
    const user = userEvent.setup()
    const task = { id: 1, instance_id: 1 }
    inboxRows = [
      { ...leave({ id: 1, employee_name: 'Bình' }), task },
      { ...leave({ id: 2, employee_name: '' }), task },
      { ...leave({ id: 3, employee_name: 'An' }), task },
      { ...leave({ id: 4, employee_name: 'Cường' }), task },
    ] as unknown as LeaveInboxRow[]
    renderTable('/hr/leave-requests?scope=to-approve')

    expect(requestCalls.every((c) => c.sort_by === undefined)).toBe(true)
    await user.click(header('Người nghỉ'))
    //  Đơn id 2 không có tên người nghỉ: ô trống của dữ liệu luôn xuống cuối ở cả hai chiều.
    expect(renderedCodes()).toEqual(['NP-3', 'NP-1', 'NP-4', 'NP-2'])
    await user.click(header('Người nghỉ'))
    expect(renderedCodes()).toEqual(['NP-4', 'NP-1', 'NP-3', 'NP-2'])
  })

  it('sorts the inbox by the main leave type name shown in the cell, ignoring the +N suffix', async () => {
    const user = userEvent.setup()
    const task = { id: 1, instance_id: 1 }
    const extraLine = { id: 1, leave_type_id: 2, leave_type_name: 'Nghỉ ốm', days: 1, sort_order: 0 }
    inboxRows = [
      { ...leave({ id: 1, leave_type_name: 'Phép năm', lines: [extraLine, extraLine] }), task },
      { ...leave({ id: 2, leave_type_name: 'Không lương' }), task },
      { ...leave({ id: 3, leave_type_name: '' }), task },
    ] as unknown as LeaveInboxRow[]
    renderTable('/hr/leave-requests?scope=to-approve')

    await user.click(header('Loại nghỉ'))
    expect(renderedCodes()).toEqual(['NP-2', 'NP-1', 'NP-3'])
    await user.click(header('Loại nghỉ'))
    expect(renderedCodes()).toEqual(['NP-1', 'NP-2', 'NP-3'])
  })
})
