import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactNode } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { balanceFixture } from './leave-balance-fixture'
import { DepartmentMembersTable } from './department-members-table'
import { JobPositionHoldersPanel } from './job-position-holders-panel'
import { LeaveBalanceRequestsCard } from './leave-balance-requests-card'
import { RoomScheduleCard } from './room-schedule-card'

//  duoc-CR-748 — bốn bảng con của phân hệ Nhân sự xếp TẠI MÁY CHỦ: bấm tiêu đề cột phải đổi tham số gửi đi
//  (`sort_by` / `sort_dir`), không xếp lại phần đã tải ở trình duyệt. Chặn ở tầng hook dữ liệu để bắt đúng bộ tham số.
//  Khóa gửi lên phải nằm trong danh sách máy chủ nhận — mỗi danh sách dưới đây chép từ tệp backend ghi bên cạnh;
//  sửa một bên thì sửa cả bên kia.

const employeeCalls: Array<Record<string, unknown>> = []
const roomCalls: Array<Record<string, unknown>> = []
const leaveCalls: Array<Record<string, unknown>> = []

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAny: () => true }),
}))
vi.mock('../hooks/use-employees', () => ({
  useEmployees: (params: Record<string, unknown>) => {
    employeeCalls.push(params)
    return { data: { total: 30, items: [] }, isLoading: false, isError: false }
  },
}))
vi.mock('../hooks/use-departments', () => ({
  useDepartments: () => ({ data: { total: 0, items: [] } }),
}))
vi.mock('../hooks/use-room', () => ({
  useRoomBookings: (params: Record<string, unknown>) => {
    roomCalls.push(params)
    return { data: { total: 0, items: [] }, isLoading: false, isError: false }
  },
}))
vi.mock('../hooks/use-leave', () => ({
  useLeaveRequests: (params: Record<string, unknown>) => {
    leaveCalls.push(params)
    return { data: { total: 0, items: [] }, isLoading: false, isError: false }
  },
}))

function wrap(node: ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>{node}</MemoryRouter>
    </QueryClientProvider>,
  )
}

const last = (calls: Array<Record<string, unknown>>) => calls[calls.length - 1]

function header(text: string) {
  return screen.getByText(text, { selector: 'thead span' })
}

async function expectHeadersSend(
  calls: Array<Record<string, unknown>>,
  cases: [header: string, key: string][],
) {
  const user = userEvent.setup()
  for (const [text, key] of cases) {
    await user.click(header(text))
    expect(last(calls), text).toMatchObject({ sort_by: key, sort_dir: 'asc' })
  }
}

beforeEach(() => {
  employeeCalls.length = 0
  roomCalls.length = 0
  leaveCalls.length = 0
})

describe('DepartmentMembersTable', () => {
  it('sends every sortable header key that `employee/sort_expressions.py` accepts', async () => {
    wrap(<DepartmentMembersTable departmentId={4} />)
    expect(last(employeeCalls).sort_by).toBeUndefined()
    await expectHeadersSend(employeeCalls, [
      ['Mã NV', 'code'],
      ['Họ tên', 'full_name'],
      ['Chức danh', 'position'],
      ['Tình trạng', 'status'],
    ])
    expect(last(employeeCalls).department_id).toBe(4)
  })

  it('cycles asc -> desc -> off and goes back to page 1 on every change', async () => {
    const user = userEvent.setup()
    wrap(<DepartmentMembersTable departmentId={4} />)
    await user.click(screen.getByRole('button', { name: 'Trang sau' }))
    expect(last(employeeCalls).page).toBe(2)

    await user.click(header('Họ tên'))
    expect(last(employeeCalls)).toMatchObject({ sort_by: 'full_name', sort_dir: 'asc', page: 1 })
    await user.click(header('Họ tên'))
    expect(last(employeeCalls)).toMatchObject({ sort_by: 'full_name', sort_dir: 'desc' })
    await user.click(header('Họ tên'))
    expect(last(employeeCalls).sort_by).toBeUndefined()
    expect(last(employeeCalls).sort_dir).toBeUndefined()
  })
})

describe('JobPositionHoldersPanel', () => {
  it('sends the four column keys to the server, department by NAME (department_name)', async () => {
    wrap(<JobPositionHoldersPanel positionId={3} />)
    await expectHeadersSend(employeeCalls, [
      ['Mã NV', 'code'],
      ['Họ tên', 'full_name'],
      ['Phòng ban', 'department_name'],
      ['Tình trạng', 'status'],
    ])
    expect(last(employeeCalls).position_id).toBe(3)
  })
})

describe('RoomScheduleCard', () => {
  it('keeps the default start_at order until a header is clicked, then sends that key instead', async () => {
    wrap(<RoomScheduleCard roomId={8} />)
    //  Hai bảng (Sắp tới · Đã qua) cùng gọi một hook: lượt gọi đầu là Sắp tới, lượt sau là Đã qua.
    expect(roomCalls.slice(0, 2).map((p) => [p.sort_by, p.sort_dir])).toEqual([
      ['start_at', 'asc'],
      ['start_at', 'desc'],
    ])
    const user = userEvent.setup()
    await user.click(header('Người đặt'))
    const upcoming = roomCalls.filter((p) => 'from_time' in p)
    const past = roomCalls.filter((p) => 'to_time' in p)
    expect(last(upcoming)).toMatchObject({ sort_by: 'requester_name', sort_dir: 'asc' })
    //  Bảng Đã qua không bị kéo theo: thứ tự của nó vẫn là mặc định.
    expect(last(past)).toMatchObject({ sort_by: 'start_at', sort_dir: 'desc' })
  })

  it('offers only keys `meeting_room/sort_expressions.py` or the booking table can sort', async () => {
    wrap(<RoomScheduleCard roomId={8} />)
    const upcoming = () => roomCalls.filter((p) => 'from_time' in p)
    const user = userEvent.setup()
    for (const [text, key] of [
      ['Ngày', 'start_at'],
      ['Nội dung', 'title'],
      ['Người đặt', 'requester_name'],
      ['Trạng thái', 'status'],
      ['Số phiếu', 'code'],
    ] as const) {
      await user.click(header(text))
      expect(last(upcoming()), text).toMatchObject({ sort_by: key })
      //  Về lại "thôi xếp" cho cột kế tiếp bắt đầu từ chiều tăng.
      await user.click(header(text))
      await user.click(header(text))
    }
    //  "Khung giờ" không có cột riêng ở máy chủ: bấm không đổi gì.
    const before = roomCalls.length
    await user.click(header('Khung giờ'))
    expect(roomCalls.length).toBe(before)
  })
})

describe('LeaveBalanceRequestsCard', () => {
  it('sends each sortable header to the leave-request list and keeps the balance filters', async () => {
    wrap(<LeaveBalanceRequestsCard balance={balanceFixture({ employee_id: 2, leave_type_id: 1, year: 2026 })} />)
    await expectHeadersSend(leaveCalls, [
      ['Số đơn', 'code'],
      ['Trạng thái', 'status'],
      ['Từ ngày', 'from_date'],
      ['Đến ngày', 'to_date'],
      ['Số ngày', 'total_days'],
      ['Lý do', 'reason'],
    ])
    expect(last(leaveCalls)).toMatchObject({ employee_id: '2', leave_type_id: '1', from_date: '2026-01-01' })
  })
})
