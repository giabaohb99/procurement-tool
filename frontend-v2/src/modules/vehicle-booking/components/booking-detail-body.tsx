import { MapPin } from 'lucide-react'

import { Card } from '@/shared/ui/card'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { formatMoney } from '@/shared/utils/format-money'
import { REQUEST_TYPE, type VehicleBooking } from '../types/vehicle-booking'
import { CarBookingIcon, DeliveryBookingIcon } from './booking-type-icons'
import { DriverStatusBadge } from './status-pill'

/** Chuỗi ISO không kèm múi giờ (vd "2026-09-01T08:00") → hiển thị gọn dd/mm/yyyy hh:mm. */
function formatDateTime(value: string): string {
  if (!value) return ''
  const [date, time] = value.split('T')
  if (!date) return value
  const [y, m, d] = date.split('-')
  const hm = (time ?? '').slice(0, 5)
  return `${d}/${m}/${y}${hm ? ` ${hm}` : ''}`
}

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="border-b pb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
      {children}
    </h3>
  )
}

function InfoRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      <ReadOnlyValue>{children}</ReadOnlyValue>
    </div>
  )
}

/**
 * Thân chi tiết phiếu đặt xe (các thẻ Lộ trình / Thông tin / Điều phối). Dùng chung
 * cho cả trang chi tiết `/vehicle-booking/:id` LẪN popup mở từ danh sách — nên đặt
 * riêng ở đây, không nằm trong page.
 */
export function BookingDetailBody({ booking }: { booking: VehicleBooking }) {
  const isDelivery = booking.request_type === REQUEST_TYPE.delivery
  const dispatched =
    booking.assigned_vehicle_id ||
    booking.assigned_driver_id ||
    booking.driver_status ||
    booking.distance_km ||
    booking.cost

  return (
    <>
      <Card className="flex flex-col gap-4 p-5">
        <div className="flex items-center justify-between">
          <span className="inline-flex items-center gap-2 font-medium">
            {isDelivery ? (
              <DeliveryBookingIcon className="size-5 text-orange-600 dark:text-orange-400" />
            ) : (
              <CarBookingIcon className="size-5 text-sky-600 dark:text-sky-400" />
            )}
            {booking.request_type_label}
          </span>
          {/* Badge trạng thái đã hiển thị ở tiêu đề trang — không lặp lại ở đây. */}
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <InfoRow label="Mã phiếu">{booking.code}</InfoRow>
          <InfoRow label="Người tạo">{booking.requester}</InfoRow>
          <InfoRow label="Hình thức">
            {booking.is_self_drive ? 'Tự lái (người yêu cầu là tài xế)' : 'Có tài xế điều phối'}
          </InfoRow>
          <InfoRow label="Mục đích">{booking.purpose}</InfoRow>
          {booking.is_self_drive && (
            <InfoRow label="GPLX người lái">
              {[booking.license_number, booking.license_class].filter(Boolean).join(' · ') || '—'}
            </InfoRow>
          )}
        </div>
      </Card>

      {/* Lộ trình */}
      <Card className="flex flex-col gap-4 p-5">
        <SectionHeading>Lộ trình</SectionHeading>
        <div className="grid gap-4 sm:grid-cols-2">
          <InfoRow label={isDelivery ? 'Điểm lấy hàng' : 'Điểm đi'}>{booking.start_location}</InfoRow>
          <InfoRow label={isDelivery ? 'Điểm giao hàng' : 'Điểm đến'}>{booking.end_location}</InfoRow>
        </div>
        {booking.stops.length > 0 && (
          <div className="flex flex-col gap-2">
            <span className="text-xs text-muted-foreground">Điểm dừng trung gian</span>
            {booking.stops.map((stop, index) => (
              <div key={index} className="flex items-start gap-2 rounded-lg border p-2.5 text-sm">
                <MapPin className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                <div className="flex flex-col">
                  <span>{stop.location}</span>
                  {(stop.contact_name || stop.contact_phone) && (
                    <span className="text-xs text-muted-foreground">
                      {[stop.contact_name, stop.contact_phone].filter(Boolean).join(' · ')}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
        <div className="grid gap-4 sm:grid-cols-2">
          <InfoRow label={isDelivery ? 'Thời gian lấy hàng' : 'Thời gian đi'}>
            {formatDateTime(booking.start_time)}
          </InfoRow>
          <InfoRow label={isDelivery ? 'Thời gian giao (dự kiến)' : 'Thời gian về (dự kiến)'}>
            {formatDateTime(booking.end_time)}
          </InfoRow>
        </div>
        {!isDelivery && <InfoRow label="Khứ hồi">{booking.is_round_trip ? 'Có' : 'Không'}</InfoRow>}
      </Card>

      {/* Khối riêng theo loại */}
      {isDelivery ? (
        <Card className="flex flex-col gap-4 p-5">
          <SectionHeading>Thông tin giao hàng</SectionHeading>
          <div className="grid gap-4 sm:grid-cols-2">
            <InfoRow label="Tên hàng hóa">{booking.goods_name}</InfoRow>
            <InfoRow label="Kích thước / Khối lượng">{booking.goods_size}</InfoRow>
            <InfoRow label="Người gửi">{booking.sender_name}</InfoRow>
            <InfoRow label="SĐT người gửi">{booking.sender_phone}</InfoRow>
            <InfoRow label="Người nhận">{booking.receiver_name}</InfoRow>
            <InfoRow label="SĐT người nhận">{booking.receiver_phone}</InfoRow>
          </div>
          <InfoRow label="Chỉ dẫn đặc biệt">{booking.special_instructions}</InfoRow>
        </Card>
      ) : (
        <Card className="flex flex-col gap-4 p-5">
          <SectionHeading>Thông tin chuyến đi</SectionHeading>
          <div className="grid gap-4 sm:grid-cols-2">
            <InfoRow label="Số hành khách">{booking.passenger_count}</InfoRow>
            <InfoRow label="SĐT liên hệ">{booking.contact_phone}</InfoRow>
          </div>
          <InfoRow label="Người tham gia">{booking.attendees}</InfoRow>
        </Card>
      )}

      {/* Điều phối & chạy chuyến — chỉ hiện khi đã có */}
      {dispatched ? (
        <Card className="flex flex-col gap-4 p-5">
          <SectionHeading>Điều phối &amp; chuyến đi</SectionHeading>
          <div className="grid gap-4 sm:grid-cols-2">
            <InfoRow label="Xe được phân">{booking.assigned_vehicle_label}</InfoRow>
            <InfoRow label="Tài xế được phân">{booking.assigned_driver_label}</InfoRow>
            <InfoRow label="Trạng thái tài xế">
              <DriverStatusBadge status={booking.driver_status} label={booking.driver_status_label} />
            </InfoRow>
            <InfoRow label="Thời gian điều phối">{formatDateTime(booking.dispatched_at ?? '')}</InfoRow>
            <InfoRow label="Bắt đầu thực tế">{formatDateTime(booking.actual_start_time)}</InfoRow>
            <InfoRow label="Kết thúc thực tế">{formatDateTime(booking.actual_end_time)}</InfoRow>
            <InfoRow label="Số km">{booking.distance_km ? String(booking.distance_km) : '—'}</InfoRow>
            <InfoRow label="Chi phí">{booking.cost ? formatMoney(booking.cost) : '—'}</InfoRow>
          </div>
        </Card>
      ) : null}

      {booking.note && (
        <Card className="flex flex-col gap-2 p-5">
          <SectionHeading>Ghi chú</SectionHeading>
          <ReadOnlyValue multiline>{booking.note}</ReadOnlyValue>
        </Card>
      )}
    </>
  )
}
