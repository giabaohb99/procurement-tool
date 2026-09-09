import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import type { RoomGlance } from '../hooks/use-hr-room-glance'
import type { RoomBooking } from '../types/room'
import { RoomGlanceCard } from './room-glance-card'

function makeBooking(overrides: Partial<RoomBooking> = {}): RoomBooking {
  return {
    id: 1,
    code: 'PH001',
    room_id: 1,
    room_name: 'Phòng họp 301',
    room_code: 'P301',
    company_id: 1,
    department_id: 1,
    requester_employee_id: 1,
    requester_name: 'Trần Thị A',
    title: 'Họp giao ban tuần',
    purpose: '',
    start_at: '2026-09-05T09:00:00',
    end_at: '2026-09-05T10:00:00',
    attendee_count: 4,
    status: 3,
    status_label: 'Đã duyệt',
    approval_instance_id: 0,
    submitted_at: null,
    decided_at: null,
    decision_note: '',
    ...overrides,
  }
}

function makeGlance(overrides: Partial<RoomGlance> = {}): RoomGlance {
  return { today: [], pending: 0, canRead: true, isLoading: false, ...overrides }
}

function renderCard(glance: RoomGlance, now: Date) {
  return render(
    <MemoryRouter>
      <RoomGlanceCard glance={glance} now={now} />
    </MemoryRouter>,
  )
}

describe('RoomGlanceCard', () => {
  it('gắn dấu «Đang họp» cho cuộc đang diễn ra, không gắn cho cuộc vừa tan', () => {
    // Mốc kết thúc là biên HỞ: 10:00 tức đã tan, không còn "đang họp".
    renderCard(
      makeGlance({
        today: [
          makeBooking({ id: 1, title: 'Đang chạy' }),
          makeBooking({
            id: 2,
            title: 'Vừa tan',
            start_at: '2026-09-05T08:00:00',
            end_at: '2026-09-05T09:30:00',
          }),
        ],
      }),
      new Date(2026, 8, 5, 9, 30),
    )

    expect(screen.getAllByText('Đang họp')).toHaveLength(1)
  })

  it('chưa tới giờ thì không phải «Đang họp»', () => {
    renderCard(
      makeGlance({ today: [makeBooking()] }),
      new Date(2026, 8, 5, 8, 59),
    )

    expect(screen.queryByText('Đang họp')).not.toBeInTheDocument()
  })

  it('quá 6 dòng thì đếm lại phần dư thay vì cắt lặng lẽ', () => {
    const today = Array.from({ length: 9 }, (_, index) =>
      makeBooking({ id: index + 1, title: `Cuộc ${index + 1}` }),
    )

    renderCard(makeGlance({ today }), new Date(2026, 8, 5, 7, 0))

    expect(screen.getByText('Cuộc 6')).toBeInTheDocument()
    expect(screen.queryByText('Cuộc 7')).not.toBeInTheDocument()
    expect(screen.getByText('Và 3 cuộc nữa.')).toBeInTheDocument()
  })

  it('hết phiếu chờ duyệt thì bỏ hẳn dòng đó, không hiện "0 phiếu"', () => {
    renderCard(makeGlance({ today: [makeBooking()], pending: 0 }), new Date())

    expect(screen.queryByText(/phiếu chờ duyệt/)).not.toBeInTheDocument()
  })

  it('thiếu quyền thì nói rõ là THIẾU QUYỀN, không nói "chưa có cuộc họp nào"', () => {
    // Hai câu đó dẫn tới hai hành động khác hẳn nhau: một bên đi xin quyền, một
    // bên yên tâm là hôm nay rảnh.
    renderCard(makeGlance({ canRead: false }), new Date())

    expect(screen.getByText('Bạn không có quyền xem phiếu đặt phòng.')).toBeInTheDocument()
    expect(screen.queryByText('Hôm nay chưa có cuộc họp nào.')).not.toBeInTheDocument()
  })

  it('không có phiếu nào thì hiện câu rỗng riêng của thẻ', () => {
    renderCard(makeGlance(), new Date())

    expect(screen.getByText('Hôm nay chưa có cuộc họp nào.')).toBeInTheDocument()
  })

  it('hôm nay trống VẪN giữ dòng chân: số phiếu chờ duyệt và link lịch', () => {
    // Bản đầu dùng `isEmpty` của `ChartCard` — nó thay THẲNG cả khối con nên
    // dòng chân biến mất, tức con số phải-đi-ký bị giấu đúng vào hôm người
    // duyệt rảnh nhất để ký.
    renderCard(makeGlance({ today: [], pending: 22 }), new Date())

    expect(screen.getByText('Hôm nay chưa có cuộc họp nào.')).toBeInTheDocument()
    expect(screen.getByText('22 phiếu chờ duyệt')).toBeInTheDocument()
    expect(screen.getByText('Mở lịch phòng họp')).toBeInTheDocument()
  })

  it('thiếu tên phòng thì lùi về MÃ phòng, không để trống', () => {
    renderCard(
      makeGlance({ today: [makeBooking({ room_name: '' })] }),
      new Date(2026, 8, 5, 7, 0),
    )

    expect(screen.getByText(/P301/)).toBeInTheDocument()
  })
})
