import { ArrowLeft, MapPin } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'

import { AuditTimeline } from '@/shared/audit/audit-timeline'
import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { formatMoney } from '@/shared/utils/format-money'
import { CarBookingIcon, DeliveryBookingIcon } from '../components/booking-type-icons'
import { useVehicleBooking } from '../hooks/use-vehicle-bookings'
import {
  BOOKING_STATUS_LABELS,
  BOOKING_STATUS_TONE,
  DRIVER_STATUS_LABELS,
  REQUEST_TYPE,
  type VehicleBooking,
} from '../types/vehicle-booking'

const TONE_VARIANT: Record<string, 'secondary' | 'default' | 'destructive' | 'outline'> = {
  neutral: 'secondary',
  info: 'default',
  success: 'default',
  warning: 'outline',
  danger: 'destructive',
}

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

export function VehicleBookingDetailPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const bookingId = Number(id)
  const { data, isLoading, isError } = useVehicleBooking(Number.isFinite(bookingId) ? bookingId : null)

  return (
    <PageContainer>
      <PageHeader
        title={data ? `Yêu cầu đặt xe ${data.code}` : 'Chi tiết yêu cầu đặt xe'}
        description={data?.purpose}
        actions={
          <Button variant="ghost" onClick={() => navigate(appRoutes.vehicleBooking.root)}>
            <ArrowLeft className="size-4" />
            Quay lại
          </Button>
        }
      />

      {isLoading && <p className="text-sm text-muted-foreground">Đang tải…</p>}
      {isError && (
        <p className="text-sm text-destructive">
          Không tải được yêu cầu. Kiểm tra kết nối hoặc quyền truy cập.
        </p>
      )}

      {data && (
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-5">
          <BookingBody booking={data} />
          <Card className="flex flex-col gap-3 p-5">
            <SectionHeading>Lịch sử thao tác</SectionHeading>
            <AuditTimeline entity="vehicle_booking" entityId={data.id} />
          </Card>
        </div>
      )}
    </PageContainer>
  )
}

function BookingBody({ booking }: { booking: VehicleBooking }) {
  const isDelivery = booking.request_type === REQUEST_TYPE.delivery
  const tone = TONE_VARIANT[BOOKING_STATUS_TONE[booking.status] ?? 'neutral']
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
          <Badge variant={tone}>
            {booking.status_label || BOOKING_STATUS_LABELS[booking.status] || '—'}
          </Badge>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <InfoRow label="Mã phiếu">{booking.code}</InfoRow>
          <InfoRow label="Người tạo">{booking.requester}</InfoRow>
          <InfoRow label="Mục đích">{booking.purpose}</InfoRow>
        </div>
      </Card>

      {/* Lộ trình */}
      <Card className="flex flex-col gap-4 p-5">
        <SectionHeading>Lộ trình</SectionHeading>
        <div className="grid gap-4 sm:grid-cols-2">
          <InfoRow label={isDelivery ? 'Điểm lấy hàng' : 'Điểm đi'}>
            {booking.start_location}
          </InfoRow>
          <InfoRow label={isDelivery ? 'Điểm giao hàng' : 'Điểm đến'}>
            {booking.end_location}
          </InfoRow>
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
        {!isDelivery && (
          <InfoRow label="Khứ hồi">{booking.is_round_trip ? 'Có' : 'Không'}</InfoRow>
        )}
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
            <InfoRow label="Trạng thái tài xế">
              {DRIVER_STATUS_LABELS[booking.driver_status] || '—'}
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
