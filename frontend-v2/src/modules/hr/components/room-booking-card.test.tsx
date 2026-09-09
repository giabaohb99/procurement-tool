import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { RoomBookingCard } from './room-booking-card'
import { ROOM_BOOKING_STATUS, type RoomBooking } from '../types/room'

function booking(overrides: Partial<RoomBooking> = {}): RoomBooking {
  return {
    id: 1,
    code: 'PH113',
    room_id: 2,
    room_name: 'Phòng họp 302',
    room_code: 'P302',
    company_id: 1,
    department_id: 1,
    requester_employee_id: 1,
    requester_name: 'Dego Admin',
    title: 'Họp giao ban',
    purpose: '',
    start_at: '2026-10-10T09:00:00',
    end_at: '2026-10-10T10:00:00',
    attendee_count: 3,
    status: ROOM_BOOKING_STATUS.PENDING,
    status_label: 'Chờ duyệt',
    approval_instance_id: 0,
    submitted_at: null,
    decided_at: null,
    decision_note: '',
    ...overrides,
  }
}

/**
 * Chữ của DÒNG CHÂN, gộp khoảng trắng — dòng chứa mã phiếu.
 *
 * ⚠️ Đừng đếm mọi `<span aria-hidden>` chứa dấu `·` trong thẻ: dòng ngày giờ
 * cũng dùng đúng dấu đó, nên phép đếm ấy luôn dôi một và bài kiểm đỏ vì bản
 * thân nó sai, không phải vì mã sai.
 */
function footerTextOf(code: string): string {
  const footer = screen.getByText(code).parentElement
  return (footer?.textContent ?? '').replace(/\s+/g, ' ').trim()
}

describe('RoomBookingCard', () => {
  it('bày đủ bốn thứ nhận ra một phiếu: nội dung · phòng · ngày giờ · mã', () => {
    render(<RoomBookingCard booking={booking()} />)

    expect(screen.getByText('Họp giao ban')).toBeInTheDocument()
    expect(screen.getByText('Phòng họp 302')).toBeInTheDocument()
    expect(screen.getByText('10/10/2026')).toBeInTheDocument()
    expect(screen.getByText(/09:00 – 10:00/)).toBeInTheDocument()
    expect(screen.getByText('PH113')).toBeInTheDocument()
  })

  it('phiếu chưa đặt tên cuộc họp thì lấy MÃ thay, không để trống dòng đầu', () => {
    //  `title` không bắt buộc ở tầng nhập. Để trống thì thẻ mở đầu bằng một
    //  khoảng trắng và người dùng không biết mình đang nhìn phiếu nào.
    render(<RoomBookingCard booking={booking({ title: '' })} />)

    //  Hai chỗ: dòng đầu (thay tiêu đề) và dòng chân.
    expect(screen.getAllByText('PH113')).toHaveLength(2)
  })

  it('phòng đã bị xóa khỏi danh mục thì lùi về mã phòng rồi tới id', () => {
    render(<RoomBookingCard booking={booking({ room_name: '', room_code: 'P302' })} />)
    expect(screen.getByText('P302')).toBeInTheDocument()

    render(<RoomBookingCard booking={booking({ room_name: '', room_code: '' })} />)
    expect(screen.getByText('#2')).toBeInTheDocument()
  })

  it('tab «Cần tôi duyệt» tắt huy hiệu trạng thái và bày HẠN XỬ LÝ thay vào', () => {
    //  Mọi phiếu ở tab đó đều «Chờ duyệt» nên huy hiệu chỉ lặp lại; hạn xử lý
    //  mới là thứ phân biệt hai việc đang chờ cùng một người.
    render(
      <RoomBookingCard
        booking={booking()}
        showStatus={false}
        dueAt="2026-10-08T17:00:00"
      />,
    )

    expect(screen.queryByText('Chờ duyệt')).not.toBeInTheDocument()
    expect(screen.getByText(/Hạn xử lý/)).toBeInTheDocument()
  })

  it('không có hạn xử lý thì KHÔNG bỏ lại dấu chấm giữa mồ côi ở dòng chân', () => {
    //  Dấu `·` nối hai vế; thiếu vế sau mà vẫn in dấu thì dòng chân kết thúc
    //  bằng một chấm treo lơ lửng, đọc ra như dữ liệu bị cắt mất.
    render(<RoomBookingCard booking={booking()} />)
    //  Không có dấu cách giữa các vế vì khoảng hở là `gap-x-2` của flex, không
    //  phải ký tự — đây là chữ thô, không phải thứ người dùng nhìn thấy.
    expect(footerTextOf('PH113')).toBe('PH113·Dego Admin')
  })

  it('người đặt trống thì bỏ luôn vế đó, không để dấu phân cách đứng một mình', () => {
    render(<RoomBookingCard booking={booking({ requester_name: '' })} />)
    expect(footerTextOf('PH113')).toBe('PH113')
  })

  it('lý do từ chối / trả về hiện thẳng thành CHỮ, không giấu trong tooltip', () => {
    //  Màn cảm ứng không có nhịp «rê chuột»: tooltip hoặc không mở được, hoặc
    //  mở ra rồi che mất chính dòng vừa bấm.
    render(
      <RoomBookingCard
        booking={booking({
          status: ROOM_BOOKING_STATUS.REJECTED,
          status_label: 'Từ chối',
          decision_note: 'Phòng đã có lịch tiếp khách',
        })}
      />,
    )

    expect(screen.getByText('Phòng đã có lịch tiếp khách')).toBeInTheDocument()
  })
})
