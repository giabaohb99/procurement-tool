import { formatMoney } from '@/shared/utils/format-money'
import { BOOKING_STATUS, type VehicleBooking } from '../types/vehicle-booking'
import { formatStamp } from './booking-time-format'

/**
 * Trạng thái một chặng xử lý:
 * · `done` — đã xảy ra · `pending` — chưa tới lượt · `stopped` — phiếu dừng ở đây.
 */
export type StageState = 'done' | 'pending' | 'stopped'

/** Một mẩu thông tin phụ của chặng ("Xe · 51A-12345"). Giá trị rỗng bị loại. */
export interface StageFact {
  label: string
  value: string
}

export interface BookingStage {
  key: string
  title: string
  state: StageState
  /** Mốc thời gian đã xảy ra, đã định dạng; rỗng khi chưa tới chặng. */
  time: string
  /** Người thực hiện chặng; rỗng khi chưa có. */
  actor: string
  facts: StageFact[]
}

/**
 * Dựng TIẾN TRÌNH của phiếu đặt xe: Tạo phiếu → Phê duyệt → Điều phối → Hoàn thành.
 *
 * Bản trước bày mười ô "Người phê duyệt / Ngày duyệt / Người điều phối / …" cạnh
 * nhau, và phiếu mới thì cả mười đều RỖNG — mười cái khung trống chiếm đúng bằng
 * chỗ của dữ liệu thật, trong khi thứ người đọc cần biết chỉ là *phiếu đang đứng ở
 * đâu*. Xếp theo chặng thì ô trống trở thành câu trả lời ("Chờ điều phối") chứ
 * không còn là chỗ trống.
 *
 * Hàm THUẦN, không đụng React — để bài kiểm chạy thẳng vào luật nghiệp vụ.
 */
export function buildBookingStages(booking: VehicleBooking): BookingStage[] {
  const s = booking.status
  const rejected = s === BOOKING_STATUS.rejected
  const returned = s === BOOKING_STATUS.returned
  const cancelled = s === BOOKING_STATUS.cancelled

  const stages: BookingStage[] = [
    {
      key: 'created',
      title: 'Tạo phiếu',
      state: 'done',
      time: formatStamp(booking.created_at),
      actor: booking.requester,
      facts: [],
    },
  ]

  //  Chặng DUYỆT. Dùng trạng thái phiếu làm nguồn chính chứ không dựa vào
  //  `approved_at`: phiếu chạy qua luồng duyệt nhiều bước được backend đẩy sang
  //  "Đã duyệt" mà không ghi mốc duyệt một-bước, nên xem mốc là điều kiện thì
  //  phiếu đã duyệt xong vẫn hiện "Chờ duyệt".
  const approved =
    Boolean(booking.approved_at) ||
    s === BOOKING_STATUS.approved ||
    s === BOOKING_STATUS.dispatched ||
    s === BOOKING_STATUS.completed

  if (rejected || returned) {
    stages.push({
      key: 'approve',
      title: rejected ? 'Bị từ chối' : 'Trả về yêu cầu chỉnh sửa',
      state: 'stopped',
      time: formatStamp(booking.approved_at),
      actor: booking.approver_name,
      facts: [],
    })
    return stages
  }

  stages.push({
    key: 'approve',
    title: approved ? 'Đã phê duyệt' : 'Chờ phê duyệt',
    state: approved ? 'done' : 'pending',
    time: formatStamp(booking.approved_at),
    actor: booking.approver_name,
    facts: [],
  })

  //  Chặng ĐIỀU PHỐI. Tự lái thì điều phối chỉ gán XE, không có tài xế — nói
  //  thẳng ra nhãn, vì dòng "Tài xế —" ở phiếu tự lái đọc ra là *quên gán tài xế*.
  const dispatched =
    Boolean(booking.dispatched_at) ||
    Boolean(booking.assigned_vehicle_label) ||
    s === BOOKING_STATUS.dispatched ||
    s === BOOKING_STATUS.completed

  stages.push({
    key: 'dispatch',
    title: dispatched
      ? booking.is_self_drive
        ? 'Đã bố trí xe (tự lái)'
        : 'Đã điều phối'
      : 'Chờ điều phối',
    state: dispatched ? 'done' : 'pending',
    time: formatStamp(booking.dispatched_at),
    actor: booking.dispatched_by_name,
    facts: keepFilled([
      { label: 'Xe', value: booking.assigned_vehicle_label },
      { label: 'Tài xế', value: booking.is_self_drive ? '' : booking.assigned_driver_label },
    ]),
  })

  const completed = s === BOOKING_STATUS.completed || Boolean(booking.actual_end_time)

  stages.push({
    key: 'complete',
    title: completed ? 'Hoàn thành chuyến' : 'Chưa hoàn thành',
    state: completed ? 'done' : 'pending',
    time: formatStamp(booking.actual_end_time),
    actor: '',
    facts: keepFilled([
      { label: 'Khởi hành thực tế', value: formatStamp(booking.actual_start_time) },
      //  `distance_km` và `cost` là SỐ: `0` nghĩa "chưa nhập" ở nghiệp vụ này
      //  (không ai chạy 0 km), nên để rỗng thay vì bày "0 km · 0 đ".
      { label: 'Số km', value: booking.distance_km ? `${booking.distance_km} km` : '' },
      { label: 'Chi phí', value: booking.cost ? `${formatMoney(booking.cost)} đ` : '' },
    ]),
  })

  //  Phiếu ĐÃ HỦY thì những chặng chưa tới lượt sẽ không bao giờ tới nữa — giữ
  //  lại "Chờ điều phối" bên dưới dòng "Đã hủy" là hứa một việc đã chết.
  if (cancelled) {
    return [
      ...stages.filter((stage) => stage.state !== 'pending'),
      { key: 'cancel', title: 'Đã hủy phiếu', state: 'stopped', time: '', actor: '', facts: [] },
    ]
  }

  return stages
}

function keepFilled(facts: StageFact[]): StageFact[] {
  return facts.filter((fact) => Boolean(fact.value))
}
