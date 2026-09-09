import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { RoomDayList } from './room-day-list'
import { ROOM_BOOKING_STATUS, type MeetingRoom, type RoomBooking } from '../types/room'

function room(overrides: Partial<MeetingRoom> = {}): MeetingRoom {
  return {
    id: 1,
    code: 'P301',
    name: 'Phòng họp 301',
    company_id: 1,
    location: 'Tầng 3',
    capacity: 8,
    equipment: '',
    is_active: true,
    sort_order: 0,
    note: '',
    ...overrides,
  }
}

function booking(overrides: Partial<RoomBooking> = {}): RoomBooking {
  return {
    id: 1,
    code: 'DP001',
    room_id: 1,
    room_name: 'Phòng họp 301',
    room_code: 'P301',
    company_id: 1,
    department_id: 1,
    requester_employee_id: 1,
    requester_name: 'Dego Admin',
    title: 'Họp giao ban',
    purpose: '',
    start_at: '2026-09-05T09:00:00',
    end_at: '2026-09-05T10:00:00',
    attendee_count: 3,
    status: ROOM_BOOKING_STATUS.APPROVED,
    status_label: 'Đã duyệt',
    approval_instance_id: 0,
    submitted_at: null,
    decided_at: null,
    decision_note: '',
    ...overrides,
  }
}

const ROOMS = [
  room({ id: 1, name: 'Phòng họp 301' }),
  room({ id: 2, name: 'Phòng họp 302', location: 'Tầng 3', capacity: 12 }),
  room({ id: 3, name: 'Phòng họp 201', location: 'Tầng 2', capacity: 20 }),
]

describe('RoomDayList', () => {
  it('ngày chưa ai đặt gì thì nói bằng MỘT câu, không lặp lại từng phòng', () => {
    //  Bản đầu đổ tất cả vào một danh sách phẳng nên ngày trống ra 21 dòng giống
    //  hệt nhau cùng nói «Trống cả ngày» — người dùng cuộn hết hai chục dòng để
    //  biết một điều đáng ra nói bằng một câu (khách báo 09/09/2026).
    render(<RoomDayList rooms={ROOMS} bookings={[]} onOpenBooking={vi.fn()} />)

    expect(screen.getByText('Cả 3 phòng đều trống hôm nay')).toBeInTheDocument()
    expect(screen.queryByText(/Đang có lịch/)).not.toBeInTheDocument()
  })

  it('phòng ĐANG CÓ LỊCH đứng trên phòng còn trống', () => {
    //  Người vào xem lịch hỏi "ai đang giữ phòng nào"; câu trả lời không được
    //  nằm dưới một danh sách phòng trống dài gấp mấy lần.
    render(
      <RoomDayList
        rooms={ROOMS}
        bookings={[booking({ room_id: 2, title: 'Review thiết kế' })]}
        onOpenBooking={vi.fn()}
      />,
    )

    const busy = screen.getByText('Đang có lịch · 1 phòng')
    const free = screen.getByText('Còn trống cả ngày · 2 phòng')
    expect(busy.compareDocumentPosition(free) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  })

  it('chạm một ô phòng trống thì đặt đúng phòng đó', async () => {
    const onPickRoom = vi.fn()
    render(
      <RoomDayList
        rooms={ROOMS}
        bookings={[]}
        onOpenBooking={vi.fn()}
        onPickRoom={onPickRoom}
      />,
    )

    await userEvent.click(screen.getByRole('button', { name: 'Đặt Phòng họp 201' }))
    expect(onPickRoom).toHaveBeenCalledWith(3)
  })

  it('thiếu quyền đặt thì không mời chạm, và không có đường đặt nào', () => {
    render(
      <RoomDayList
        rooms={ROOMS}
        bookings={[booking({ room_id: 1 })]}
        onOpenBooking={vi.fn()}
      />,
    )

    expect(screen.queryByText('Chạm một phòng để đặt.')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Đặt thêm giờ khác/ })).not.toBeInTheDocument()
  })

  it('chỉ bày phiếu ĐANG GIỮ phòng — nháp, hủy, từ chối không chiếm chỗ', () => {
    //  Cùng luật với lưới và với con số «lượt giữ» trên thanh công cụ. Ba chỗ
    //  đếm khác nhau là ba con số khác nhau, và người xem không biết tin cái nào.
    render(
      <RoomDayList
        rooms={[room()]}
        bookings={[
          //  ⚠️ Tên cuộc họp phải KHÁC nhãn trạng thái: đặt trùng thì
          //  `getByText('Đã duyệt')` bắt được cả tên lẫn huy hiệu và bài kiểm đỏ
          //  vì "tìm thấy hai phần tử", chứ không phải vì mã sai.
          booking({ id: 1, title: 'Họp A', status: ROOM_BOOKING_STATUS.APPROVED }),
          booking({ id: 2, title: 'Họp B', status: ROOM_BOOKING_STATUS.PENDING }),
          booking({ id: 3, title: 'Còn nháp', status: ROOM_BOOKING_STATUS.DRAFT }),
          booking({ id: 4, title: 'Đơn đã hủy', status: ROOM_BOOKING_STATUS.CANCELLED }),
          booking({ id: 5, title: 'Bị bác', status: ROOM_BOOKING_STATUS.REJECTED }),
        ]}
        onOpenBooking={vi.fn()}
      />,
    )

    expect(screen.getByText('Họp A')).toBeInTheDocument()
    expect(screen.getByText('Họp B')).toBeInTheDocument()
    expect(screen.queryByText('Còn nháp')).not.toBeInTheDocument()
    expect(screen.queryByText('Đơn đã hủy')).not.toBeInTheDocument()
    expect(screen.queryByText('Bị bác')).not.toBeInTheDocument()
  })

  it('phòng chỉ có phiếu KHÔNG giữ chỗ vẫn được tính là còn trống', () => {
    //  Ngược lại thì phòng đó rơi vào mục «đang có lịch» với một danh sách rỗng —
    //  một khối trống trơn không nói được gì.
    render(
      <RoomDayList
        rooms={[room({ id: 1 })]}
        bookings={[booking({ id: 3, status: ROOM_BOOKING_STATUS.CANCELLED })]}
        onOpenBooking={vi.fn()}
      />,
    )

    expect(screen.getByText('Cả 1 phòng đều trống hôm nay')).toBeInTheDocument()
  })

  it('xếp phiếu theo GIỜ tăng dần, không theo thứ tự API trả về', () => {
    render(
      <RoomDayList
        rooms={[room()]}
        bookings={[
          booking({ id: 1, title: 'Chiều', start_at: '2026-09-05T14:00:00', end_at: '2026-09-05T15:00:00' }),
          booking({ id: 2, title: 'Sáng sớm', start_at: '2026-09-05T07:30:00', end_at: '2026-09-05T08:00:00' }),
        ]}
        onOpenBooking={vi.fn()}
      />,
    )

    const rows = screen.getAllByRole('listitem')
    expect(within(rows[0]).getByText('Sáng sớm')).toBeInTheDocument()
    expect(within(rows[1]).getByText('Chiều')).toBeInTheDocument()
  })

  it('phiếu của phòng KHÁC không lọt sang phòng này', () => {
    render(
      <RoomDayList
        rooms={[room({ id: 1 }), room({ id: 2, name: 'Phòng họp 302' })]}
        bookings={[booking({ id: 9, room_id: 2, title: 'Chỉ của 302' })]}
        onOpenBooking={vi.fn()}
      />,
    )

    //  Ghép nhầm phiếu là người ta tới nơi thấy có người ngồi rồi.
    expect(screen.getByText('Đang có lịch · 1 phòng')).toBeInTheDocument()
    expect(screen.getByText('Còn trống cả ngày · 1 phòng')).toBeInTheDocument()
    expect(screen.getByText('Chỉ của 302')).toBeInTheDocument()
  })

  it('bấm vào một phiếu thì mở đúng phiếu đó', async () => {
    const onOpenBooking = vi.fn()
    const row = booking({ id: 7, title: 'Review thiết kế' })
    render(<RoomDayList rooms={[room()]} bookings={[row]} onOpenBooking={onOpenBooking} />)

    await userEvent.click(screen.getByText('Review thiết kế'))
    expect(onOpenBooking).toHaveBeenCalledWith(row)
  })
})
