import { Clock, MapPin } from 'lucide-react'

import { ApprovalStageNote } from '@/modules/approval/components/approval-stage-note'
import { cn } from '@/shared/utils/cn'
import { REQUEST_TYPE, type VehicleBooking } from '../types/vehicle-booking'
import { formatTripTime } from '../utils/format-trip-time'
import { CarBookingIcon, DeliveryBookingIcon } from './booking-type-icons'
import { BookingStatusBadge } from './status-pill'

interface VehicleBookingCardProps {
  booking: VehicleBooking
  /** Bày dòng người tạo + xe / tài xế — khối hàng chờ ở Tổng quan đã gọn sẵn, chỉ danh sách cần. */
  showPeople?: boolean
}

/**
 * Một PHIẾU ĐẶT XE ở khổ điện thoại (duoc-CR-722) — xem `DataTableProps.mobileCard`. Dùng chung cho danh sách
 * phiếu và khối hàng chờ ở Tổng quan.
 *
 * ⚠️ **Mục đích lên đầu, mã phiếu tụt xuống dòng phụ** — cùng thứ bậc với `MyTripCard`: người ta nhận ra chuyến
 * bằng việc nó làm, mã chỉ dùng khi đối chiếu giấy tờ. Bảng xếp Mã phiếu trước vì đó là cột ghim.
 *
 * Lộ trình gồm cả điểm dừng như cột của bảng, chặn hai dòng: địa chỉ dài thật, để tự do thì một thẻ chiếm cả
 * màn. Không có nút trong thẻ: bảng khai `onRowClick` nên cả thẻ là một `<button>`; nút **Nhân bản** của cột
 * Thao tác nằm ở đầu trang chi tiết.
 */
export function VehicleBookingCard({ booking: b, showPeople = true }: VehicleBookingCardProps) {
  const isDelivery = b.request_type === REQUEST_TYPE.delivery
  const TypeIcon = isDelivery ? DeliveryBookingIcon : CarBookingIcon
  const route = [
    b.start_location,
    ...(b.stops ?? []).map((s) => s.location),
    b.end_location,
  ].filter(Boolean)
  const assigned = [b.assigned_vehicle_label, b.assigned_driver_label].filter(Boolean).join(' · ')

  return (
    <span className="block space-y-1.5">
      <span className="flex items-start justify-between gap-2">
        <span className="line-clamp-2 min-w-0 font-medium text-foreground">
          {b.purpose || b.request_type_label || b.code}
        </span>
        <span className="shrink-0">
          <BookingStatusBadge status={b.status} driverStatus={b.driver_status} />
        </span>
      </span>

      {/*  Dấu `·` nằm CÙNG span với vế sau — tách riêng thì lúc xuống dòng nó treo mồ côi ở mép phải. */}
      <span className="flex flex-wrap items-center gap-x-1 text-xs text-muted-foreground">
        <TypeIcon
          className={cn(
            'size-3.5 shrink-0',
            isDelivery ? 'text-orange-600 dark:text-orange-400' : 'text-sky-600 dark:text-sky-400',
          )}
          aria-hidden="true"
        />
        <span>{b.request_type_label}</span>
        <span className="font-medium text-sky-600 tabular-nums dark:text-sky-400">
          <span aria-hidden="true" className="text-muted-foreground">
            ·{' '}
          </span>
          {b.code}
        </span>
      </span>

      <span className="flex items-center gap-1.5 text-xs text-foreground/80">
        <Clock className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
        <span className="tabular-nums">{formatTripTime(b.start_time, b.end_time)}</span>
      </span>

      {route.length > 0 && (
        <span className="flex items-start gap-1.5 text-xs text-muted-foreground">
          <MapPin className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
          <span className="line-clamp-2">{route.join(' → ')}</span>
        </span>
      )}

      {showPeople && (
        <span className="block text-xs text-muted-foreground">
          {b.requester && <>{b.requester} · </>}
          {/*  Tự lái thì không có tài xế được phân — nói thẳng ra, ô trống đọc ra là "chưa bố trí xe". */}
          {assigned || (b.is_self_drive ? 'Tự lái' : 'Chưa bố trí xe')}
        </span>
      )}

      {/*  Phiếu đồng bộ từ app cũ có thể đã ký vài chặng mà huy hiệu vẫn là Chờ duyệt — cùng ghi chú như bảng. */}
      <ApprovalStageNote summary={b.approval_summary} className="max-w-full" />
    </span>
  )
}
