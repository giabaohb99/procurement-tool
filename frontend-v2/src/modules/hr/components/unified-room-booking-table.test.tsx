import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { RoomBooking, RoomInboxRow } from '../types/room'
import { UnifiedRoomBookingTable } from './unified-room-booking-table'

//  duoc-CR-744: chặn ở tầng hook dữ liệu để bắt BỘ THAM SỐ gửi đi khi bấm tiêu đề cột, và để kiểm
//  thứ tự dòng bảng đúng là thứ tự máy chủ trả về (không bị xếp lại trong từng trang).
const bookingCalls: Array<Record<string, unknown>> = []

function booking(over: Partial<RoomBooking> & { id: number }): RoomBooking {
  return {
    code: `DP-${over.id}`,
    room_id: 1,
    room_name: 'Phòng A',
    room_code: 'A',
    requester_name: `Người ${over.id}`,
    title: `Họp ${over.id}`,
    start_at: '2026-09-01T08:00:00',
    end_at: '2026-09-01T09:00:00',
    status: 2,
    status_label: 'Chờ duyệt',
    attendee_count: 0,
    ...over,
  } as RoomBooking
}

let serverRows: RoomBooking[] = []
let inboxRows: RoomInboxRow[] = []

vi.mock('../hooks/use-room', () => ({
  useRoomBookings: (params: Record<string, unknown>) => {
    bookingCalls.push(params)
    return { data: { total: serverRows.length, items: serverRows }, isLoading: false, isError: false }
  },
  useRoomToApprove: () => ({ data: { total: inboxRows.length, items: inboxRows }, isLoading: false, isError: false }),
  useRoomHandled: () => ({ data: { total: 0, items: [] }, isLoading: false, isError: false }),
  useMeetingRooms: () => ({ data: { total: 0, items: [] } }),
}))

function renderTable(url = '/hr/room-bookings') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <UnifiedRoomBookingTable />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function lastCall() {
  return bookingCalls[bookingCalls.length - 1]
}

function header(text: string) {
  return screen.getByText(text, { selector: 'thead span' })
}

function renderedCodes() {
  const body = document.querySelector('tbody') as HTMLElement
  return within(body)
    .getAllByText(/^DP-\d+$/)
    .map((el) => el.textContent)
}

beforeEach(() => {
  bookingCalls.length = 0
  serverRows = [booking({ id: 9 }), booking({ id: 7 }), booking({ id: 5 })]
  inboxRows = []
})

describe('UnifiedRoomBookingTable - sắp xếp cột (duoc-CR-744)', () => {
  it('asks the server for mine_first while no column is chosen (scope Tất cả)', () => {
    renderTable()
    expect(lastCall().mine_first).toBe(true)
    expect(lastCall().sort_by).toBeUndefined()
  })

  it('keeps the server order instead of overriding it with an id sort in the browser', () => {
    //  Trước đây trình duyệt xếp lại bằng `b.id - a.id`, đè luôn thứ tự "cuộc họp mới nhất trước" của máy chủ.
    serverRows = [booking({ id: 3 }), booking({ id: 8 }), booking({ id: 1 })]
    inboxRows = [{ ...booking({ id: 1 }), task: { id: 1 } } as unknown as RoomInboxRow]
    renderTable()
    expect(renderedCodes()).toEqual(['DP-3', 'DP-8', 'DP-1'])
  })

  it('sends sort_by to the server for each sortable header and drops mine_first', async () => {
    const user = userEvent.setup()
    renderTable()

    const cases: [string, string][] = [
      ['Số phiếu', 'code'],
      ['Trạng thái', 'status'],
      ['Nội dung cuộc họp', 'title'],
      ['Phòng', 'room_name'],
      ['Ngày họp', 'start_at'],
      ['Người đặt', 'requester_name'],
      ['Số người', 'attendee_count'],
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

    await user.click(header('Ngày họp'))
    await user.click(header('Ngày họp'))
    expect(lastCall()).toMatchObject({ sort_by: 'start_at', sort_dir: 'desc' })
    await user.click(header('Ngày họp'))
    expect(lastCall().sort_by).toBeUndefined()
    expect(lastCall().mine_first).toBe(true)
  })

  it('goes back to page 1 when the sort changes', async () => {
    const user = userEvent.setup()
    renderTable()
    await user.click(header('Phòng'))
    expect(lastCall().page).toBe(1)
  })

  it('does not ask for mine_first in the "Phiếu của tôi" scope but still sorts on the server', async () => {
    const user = userEvent.setup()
    renderTable('/hr/room-bookings?scope=mine')
    expect(lastCall().mine_first).toBeUndefined()
    await user.click(header('Ngày họp'))
    expect(lastCall()).toMatchObject({ sort_by: 'start_at', scope: 'mine' })
  })

  it('sorts the loaded inbox in the browser across the whole list (scope Cần tôi duyệt)', async () => {
    const user = userEvent.setup()
    const task = { id: 1, instance_id: 1, node_name: 'Duyệt' }
    inboxRows = [
      { ...booking({ id: 1, requester_name: 'Bình' }), task },
      { ...booking({ id: 2, requester_name: '' }), task },
      { ...booking({ id: 3, requester_name: 'An' }), task },
      { ...booking({ id: 4, requester_name: 'Cường' }), task },
    ] as unknown as RoomInboxRow[]
    renderTable('/hr/room-bookings?scope=to-approve')

    await user.click(header('Người đặt'))
    expect(renderedCodes()).toEqual(['DP-3', 'DP-1', 'DP-4', 'DP-2'])
    await user.click(header('Người đặt'))
    expect(renderedCodes()).toEqual(['DP-4', 'DP-1', 'DP-3', 'DP-2'])
  })

  it('treats an attendee count of 0 as blank (shown as a dash) when sorting the inbox', async () => {
    const user = userEvent.setup()
    const task = { id: 1, instance_id: 1, node_name: 'Duyệt' }
    inboxRows = [
      { ...booking({ id: 1, attendee_count: 0 }), task },
      { ...booking({ id: 2, attendee_count: 8 }), task },
      { ...booking({ id: 3, attendee_count: 3 }), task },
    ] as unknown as RoomInboxRow[]
    renderTable('/hr/room-bookings?scope=to-approve')

    await user.click(header('Số người'))
    expect(renderedCodes()).toEqual(['DP-3', 'DP-2', 'DP-1'])
    await user.click(header('Số người'))
    expect(renderedCodes()).toEqual(['DP-2', 'DP-3', 'DP-1'])
  })
})
