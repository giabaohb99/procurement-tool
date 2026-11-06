import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { BOOKING_STATUS, REQUEST_TYPE, type VehicleBooking } from '../types/vehicle-booking'
import { VehicleBookingCard } from './vehicle-booking-card'

//  Kiểu VehicleBooking có hơn 60 trường; thẻ chỉ đọc chừng mười cái — ép kiểu như bài kiểm có sẵn của phân hệ.
function booking(over: Partial<VehicleBooking> = {}): VehicleBooking {
  return {
    id: 941,
    code: 'DX000941',
    purpose: 'Đưa khách đi nhà máy Long An',
    request_type: REQUEST_TYPE.car,
    request_type_label: 'Đặt xe công tác',
    status: BOOKING_STATUS.pending,
    driver_status: 0,
    start_time: '2026-11-10T08:00:00',
    end_time: '2026-11-10T17:00:00',
    start_location: 'Văn phòng Dego',
    end_location: 'Nhà máy Long An',
    stops: [{ location: 'Kho Bình Chánh' }],
    requester: 'Trần Minh Được',
    assigned_vehicle_label: '51A-12345',
    assigned_driver_label: 'Nguyễn Văn Tài',
    is_self_drive: false,
    approval_summary: 'Đang ở chặng 1/1 · Người tạo chọn người duyệt',
    ...over,
  } as VehicleBooking
}

describe('VehicleBookingCard', () => {
  it('leads with the purpose and keeps type, code, time, full route, people and approval stage', () => {
    render(<VehicleBookingCard booking={booking()} />)

    expect(screen.getByText('Đưa khách đi nhà máy Long An')).toBeInTheDocument()
    expect(screen.getByText('Đặt xe công tác')).toBeInTheDocument()
    expect(screen.getByText('DX000941')).toBeInTheDocument()
    //  Lộ trình có cả điểm dừng như cột của bảng.
    expect(
      screen.getByText('Văn phòng Dego → Kho Bình Chánh → Nhà máy Long An'),
    ).toBeInTheDocument()
    expect(screen.getByText(/Trần Minh Được/)).toBeInTheDocument()
    expect(screen.getByText(/51A-12345 · Nguyễn Văn Tài/)).toBeInTheDocument()
    expect(screen.getByText('Đang ở chặng 1/1 · Người tạo chọn người duyệt')).toBeInTheDocument()
  })

  it('says self-drive or not-yet-assigned instead of leaving the vehicle line blank', () => {
    const { rerender } = render(
      <VehicleBookingCard
        booking={booking({
          assigned_vehicle_label: '',
          assigned_driver_label: '',
          is_self_drive: true,
        })}
      />,
    )
    expect(screen.getByText(/Tự lái/)).toBeInTheDocument()

    rerender(
      <VehicleBookingCard
        booking={booking({ assigned_vehicle_label: '', assigned_driver_label: '' })}
      />,
    )
    expect(screen.getByText(/Chưa bố trí xe/)).toBeInTheDocument()
  })

  it('drops the people line in the compact queue block', () => {
    render(<VehicleBookingCard booking={booking()} showPeople={false} />)

    expect(screen.queryByText(/Trần Minh Được/)).not.toBeInTheDocument()
    expect(screen.queryByText(/51A-12345/)).not.toBeInTheDocument()
  })

  it('falls back to the type label when the purpose is empty and skips an empty route', () => {
    render(
      <VehicleBookingCard
        booking={booking({ purpose: '', start_location: '', end_location: '', stops: [] })}
      />,
    )

    expect(screen.getAllByText('Đặt xe công tác')).toHaveLength(2)
    expect(screen.queryByText(/→/)).not.toBeInTheDocument()
  })

  //  Thẻ nằm trong `<button>` của DataTableMobileCards — không được chứa nút nào (nút lồng nút).
  it('renders no button of its own', () => {
    render(<VehicleBookingCard booking={booking()} />)

    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})
