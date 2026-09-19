import { describe, expect, it } from 'vitest'

import { BOOKING_STATUS, DRIVER_STATUS, type VehicleBooking } from '../types/vehicle-booking'
import { buildBookingStages } from './build-booking-stages'

/** Phiếu tối thiểu — mọi trường rỗng, từng bài tự bật lên thứ nó cần. */
function makeBooking(patch: Partial<VehicleBooking> = {}): VehicleBooking {
  return {
    id: 1,
    code: 'DX001',
    request_type: 1,
    request_type_label: 'Đặt xe công tác',
    is_self_drive: false,
    license_number: '',
    license_class: '',
    purpose: 'Đi gặp khách',
    start_location: 'Văn phòng',
    end_location: 'Sân bay',
    stops: [],
    start_time: '2026-09-10T05:00',
    end_time: '2026-09-10T08:00',
    passenger_count: 0,
    attendees: '',
    contact_phone: '',
    is_round_trip: false,
    goods_name: '',
    goods_size: '',
    sender_name: '',
    sender_phone: '',
    receiver_name: '',
    receiver_phone: '',
    special_instructions: '',
    department_id: 0,
    company_id: 0,
    first_approver_id: 0,
    requester: 'Lê Thị Ngọc Mi',
    requester_id: 9,
    requester_email: '',
    requester_phone: '',
    requester_role: '',
    status: BOOKING_STATUS.pending,
    status_label: 'Chờ duyệt',
    note: '',
    approver_name: '',
    approved_at: '',
    assigned_vehicle_id: null,
    assigned_driver_id: null,
    assigned_vehicle_label: '',
    assigned_driver_label: '',
    dispatched_by: null,
    dispatched_by_name: '',
    dispatched_at: null,
    driver_status: DRIVER_STATUS.none,
    driver_status_label: '',
    actual_start_time: '',
    actual_end_time: '',
    distance_km: 0,
    cost: 0,
    is_assigned_driver: false,
    created_at: '2026-09-01 07:30',
    ...patch,
  }
}

const titlesOf = (booking: VehicleBooking) => buildBookingStages(booking).map((s) => s.title)
const stageOf = (booking: VehicleBooking, key: string) =>
  buildBookingStages(booking).find((s) => s.key === key)

describe('buildBookingStages', () => {
  it('phiếu chờ duyệt: chỉ chặng tạo phiếu là xong, ba chặng sau còn chờ', () => {
    const stages = buildBookingStages(makeBooking())
    expect(stages.map((s) => s.state)).toEqual(['done', 'pending', 'pending', 'pending'])
    expect(titlesOf(makeBooking())).toEqual([
      'Tạo phiếu',
      'Chờ phê duyệt',
      'Chờ điều phối',
      'Chưa hoàn thành',
    ])
  })

  //  Lỗi cũ: chặng duyệt đọc `approved_at`, mà phiếu chạy qua luồng duyệt nhiều
  //  bước được đẩy sang "Đã duyệt" KHÔNG kèm mốc duyệt một-bước (đúng ca phiếu
  //  DX324 trên máy thật) — màn hình khi đó báo "Chờ phê duyệt" cho phiếu đã duyệt.
  it('trạng thái đã duyệt tính là xong dù không có mốc duyệt', () => {
    const stage = stageOf(makeBooking({ status: BOOKING_STATUS.approved }), 'approve')
    expect(stage).toMatchObject({ title: 'Đã phê duyệt', state: 'done', time: '' })
  })

  it('trạng thái sau (điều phối, hoàn thành) kéo theo chặng duyệt đã xong', () => {
    for (const status of [BOOKING_STATUS.dispatched, BOOKING_STATUS.completed]) {
      expect(stageOf(makeBooking({ status }), 'approve')?.state).toBe('done')
    }
  })

  it('từ chối và trả về cắt luôn hai chặng sau — chúng sẽ không xảy ra', () => {
    expect(titlesOf(makeBooking({ status: BOOKING_STATUS.rejected }))).toEqual([
      'Tạo phiếu',
      'Bị từ chối',
    ])
    expect(titlesOf(makeBooking({ status: BOOKING_STATUS.returned }))).toEqual([
      'Tạo phiếu',
      'Trả về yêu cầu chỉnh sửa',
    ])
    expect(stageOf(makeBooking({ status: BOOKING_STATUS.rejected }), 'approve')?.state).toBe('stopped')
  })

  it('phiếu đã hủy: bỏ mọi chặng còn chờ, khép bằng dòng Đã hủy', () => {
    const titles = titlesOf(makeBooking({ status: BOOKING_STATUS.cancelled }))
    expect(titles).toEqual(['Tạo phiếu', 'Đã hủy phiếu'])
    expect(titles.some((t) => t.startsWith('Chờ') || t.startsWith('Chưa'))).toBe(false)
  })

  it('hủy SAU khi đã duyệt vẫn giữ lại chặng đã xảy ra', () => {
    expect(
      titlesOf(makeBooking({ status: BOOKING_STATUS.cancelled, approved_at: '2026-09-02T09:00' })),
    ).toEqual(['Tạo phiếu', 'Đã phê duyệt', 'Đã hủy phiếu'])
  })

  it('điều phối: chỉ có xe (chưa gán tài xế) vẫn tính là đã điều phối', () => {
    const stage = stageOf(makeBooking({ assigned_vehicle_label: '51A-12345' }), 'dispatch')
    expect(stage?.state).toBe('done')
    expect(stage?.facts).toEqual([{ label: 'Xe', value: '51A-12345' }])
  })

  //  Phiếu TỰ LÁI không có tài xế được phân. Dòng "Tài xế —" ở đó đọc ra là
  //  *quên gán tài xế*, nên nhãn chặng phải tự nói rõ.
  it('tự lái: nhãn nói rõ chỉ bố trí xe, không dựng mẩu tài xế', () => {
    const stage = stageOf(
      makeBooking({ is_self_drive: true, assigned_vehicle_label: '51A-12345', assigned_driver_label: 'Anh Ba' }),
      'dispatch',
    )
    expect(stage?.title).toBe('Đã bố trí xe (tự lái)')
    expect(stage?.facts.map((f) => f.label)).toEqual(['Xe'])
  })

  it('km và chi phí bằng 0 coi như chưa nhập, không bày "0 km"', () => {
    const stage = stageOf(makeBooking({ status: BOOKING_STATUS.completed }), 'complete')
    expect(stage?.state).toBe('done')
    expect(stage?.facts).toEqual([])
  })

  it('km và chi phí có số thì hiện kèm đơn vị', () => {
    const stage = stageOf(
      makeBooking({ status: BOOKING_STATUS.completed, distance_km: 180, cost: 1250000 }),
      'complete',
    )
    expect(stage?.facts).toEqual([
      { label: 'Số km', value: '180 km' },
      { label: 'Chi phí', value: '1.250.000 đ' },
    ])
  })

  it('mốc thời gian đổi sang dd/mm/yyyy, nhận cả created_at có dấu cách', () => {
    const stages = buildBookingStages(
      makeBooking({ status: BOOKING_STATUS.approved, approved_at: '2026-09-02T09:15' }),
    )
    expect(stages[0]).toMatchObject({ time: '01/09/2026 07:30', actor: 'Lê Thị Ngọc Mi' })
    expect(stages[1]?.time).toBe('02/09/2026 09:15')
  })

  it('thiếu created_at thì chặng tạo phiếu không vỡ, chỉ trống mốc', () => {
    expect(buildBookingStages(makeBooking({ created_at: null }))[0]).toMatchObject({
      state: 'done',
      time: '',
    })
  })
})
