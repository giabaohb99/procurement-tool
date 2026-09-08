import { BadgeCheck, MapPin, Package, Route, Users } from 'lucide-react'

import { Card } from '@/shared/ui/card'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { cn } from '@/shared/utils/cn'
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

/**
 * Tiêu đề block chi tiết theo C-03: icon lucide (màu theme) + nhãn `font-medium`, gạch
 * dưới KÉO HẾT bề ngang thẻ (`-mx-5 px-5 border-b` bù `p-5` của Card), `-mt-1` cho
 * padding-top 16px. Card bọc dùng `p-5 pb-4` (đáy 16px).
 */
function BlockHeader({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="-mx-5 -mt-1 flex items-center justify-between border-b px-5 pb-3">
      <span className="inline-flex items-center gap-2 font-medium">
        {icon}
        {children}
      </span>
    </div>
  )
}

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="border-b pb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
      {children}
    </h3>
  )
}

function InfoRow({
  label,
  children,
  className,
}: {
  label: string
  children: React.ReactNode
  className?: string
}) {
  return (
    //  `min-w-0`: ô lưới co được dưới bề rộng một từ dài (email/URL) để không đẩy tràn lưới.
    <div className={cn('flex min-w-0 flex-col gap-1', className)}>
      <span className="text-xs text-muted-foreground">{label}</span>
      <ReadOnlyValue>{children}</ReadOnlyValue>
    </div>
  )
}

/**
 * Thân chi tiết phiếu đặt xe (các thẻ Thông tin / Phê duyệt / Lộ trình / Giao hàng).
 * Dùng chung cho cả trang chi tiết `/vehicle-booking/:id` LẪN popup mở từ danh sách —
 * nên đặt riêng ở đây, không nằm trong page. Header các block theo C-03 (icon + gạch dưới).
 */
export function BookingDetailBody({ booking }: { booking: VehicleBooking }) {
  const isDelivery = booking.request_type === REQUEST_TYPE.delivery

  return (
    <>
      {/* Block 1 — tiêu đề loại + thông tin phiếu/người tạo */}
      <Card className="flex flex-col gap-4 p-5 pb-4">
        <BlockHeader
          icon={
            isDelivery ? (
              <DeliveryBookingIcon className="size-5 text-orange-600 dark:text-orange-400" />
            ) : (
              <CarBookingIcon className="size-5 text-sky-600 dark:text-sky-400" />
            )
          }
        >
          {/*  Tự lái gộp vào nhãn loại — bỏ dòng "Hình thức" riêng (mặc định "Có tài xế
              điều phối" là dư thừa, chỉ trường hợp Tự lái mới cần nêu). */}
          {booking.request_type_label}
          {booking.is_self_drive ? ' (Tự lái)' : ''}
        </BlockHeader>
        <div className="grid gap-4 sm:grid-cols-2">
          <InfoRow label="Mã phiếu">{booking.code}</InfoRow>
          <InfoRow label="Ngày tạo">{formatDateTime((booking.created_at ?? '').replace(' ', 'T')) || '—'}</InfoRow>
          <InfoRow label="Người tạo">{booking.requester || '—'}</InfoRow>
          <InfoRow label="Email">{booking.requester_email || '—'}</InfoRow>
          <InfoRow label="Số điện thoại">{booking.requester_phone || '—'}</InfoRow>
          <InfoRow label="Vai trò">{booking.requester_role || '—'}</InfoRow>
          {/*  Mục đích trải hết 2 cột (rộng = SĐT + Vai trò) để đọc câu dài không bị cắt. */}
          <InfoRow label="Mục đích" className="sm:col-span-2">
            {booking.purpose || '—'}
          </InfoRow>
          {booking.is_self_drive && (
            <InfoRow label="GPLX người lái">
              {[booking.license_number, booking.license_class].filter(Boolean).join(' · ') || '—'}
            </InfoRow>
          )}
        </div>
      </Card>

      {/* Block 2 — Thông tin phê duyệt (duyệt · điều phối · tài xế · xe · hoàn thành · km/chi phí) */}
      <Card className="flex flex-col gap-4 p-5 pb-4">
        <BlockHeader icon={<BadgeCheck className="size-5 text-emerald-600 dark:text-emerald-400" />}>
          Thông tin phê duyệt
        </BlockHeader>
        <div className="grid gap-4 sm:grid-cols-2">
          <InfoRow label="Người phê duyệt">{booking.approver_name || '—'}</InfoRow>
          <InfoRow label="Ngày duyệt">{formatDateTime(booking.approved_at) || '—'}</InfoRow>
          <InfoRow label="Người điều phối">{booking.dispatched_by_name || '—'}</InfoRow>
          <InfoRow label="Ngày điều phối">{formatDateTime(booking.dispatched_at ?? '') || '—'}</InfoRow>
          <InfoRow label="Tài xế">{booking.assigned_driver_label || '—'}</InfoRow>
          <InfoRow label="Trạng thái tài xế">
            <DriverStatusBadge status={booking.driver_status} label={booking.driver_status_label} />
          </InfoRow>
          <InfoRow label="Xe được phân">{booking.assigned_vehicle_label || '—'}</InfoRow>
          <InfoRow label="Ngày hoàn thành yêu cầu">{formatDateTime(booking.actual_end_time) || '—'}</InfoRow>
          <InfoRow label="Số km">{booking.distance_km ? String(booking.distance_km) : '—'}</InfoRow>
          <InfoRow label="Chi phí">{booking.cost ? formatMoney(booking.cost) : '—'}</InfoRow>
        </div>
      </Card>

      {/* Lộ trình */}
      <Card className="flex flex-col gap-4 p-5 pb-4">
        <BlockHeader icon={<Route className="size-5 text-sky-600 dark:text-sky-400" />}>Lộ trình</BlockHeader>
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
        <Card className="flex flex-col gap-4 p-5 pb-4">
          <BlockHeader icon={<Package className="size-5 text-orange-600 dark:text-orange-400" />}>
            Thông tin giao hàng
          </BlockHeader>
          <div className="grid gap-4 sm:grid-cols-2">
            <InfoRow label="Tên hàng hóa">{booking.goods_name}</InfoRow>
            <InfoRow label="Kích thước / Khối lượng">{booking.goods_size}</InfoRow>
            <InfoRow label="Người gửi">{booking.sender_name}</InfoRow>
            <InfoRow label="SĐT người gửi">{booking.sender_phone}</InfoRow>
            <InfoRow label="Người nhận">{booking.receiver_name}</InfoRow>
            <InfoRow label="SĐT người nhận">{booking.receiver_phone}</InfoRow>
          </div>
        </Card>
      ) : (
        <Card className="flex flex-col gap-4 p-5 pb-4">
          <BlockHeader icon={<Users className="size-5 text-sky-600 dark:text-sky-400" />}>
            Thông tin chuyến đi
          </BlockHeader>
          <div className="grid gap-4 sm:grid-cols-2">
            <InfoRow label="Số hành khách">{booking.passenger_count}</InfoRow>
            <InfoRow label="SĐT liên hệ">{booking.contact_phone}</InfoRow>
          </div>
          <InfoRow label="Người tham gia">{booking.attendees}</InfoRow>
        </Card>
      )}

      {/*  Chỉ hiện khi ghi chú CÓ NỘI DUNG THẬT — `.trim()` để ô toàn khoảng trắng /
          xuống dòng cũng coi như rỗng, không dựng khung trống. */}
      {booking.note?.trim() && (
        <Card className="flex flex-col gap-2 p-5">
          <SectionHeading>Ghi chú</SectionHeading>
          <ReadOnlyValue multiline>{booking.note}</ReadOnlyValue>
        </Card>
      )}
    </>
  )
}
