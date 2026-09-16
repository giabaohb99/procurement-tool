import { Clock, Package, Users } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { cn } from '@/shared/utils/cn'

import { REQUEST_TYPE, type VehicleBooking } from '../types/vehicle-booking'
import { formatTripTime } from '../utils/format-trip-time'
import { BookingWorkflowActions } from './booking-workflow-actions'
import { CarBookingIcon, DeliveryBookingIcon } from './booking-type-icons'
import { BookingStatusBadge } from './status-pill'

/**
 * Thẻ MỘT CHUYẾN ở màn «Chuyến của tôi».
 *
 * Thứ bậc đọc: mục đích chuyến → thời gian → lộ trình → xe → nút. Mục đích đứng
 * đầu vì đó là thứ tài xế dùng để nhận ra chuyến; mã phiếu chỉ cần khi đối chiếu
 * giấy tờ nên lùi xuống hàng phụ.
 *
 * MỘT huy hiệu trạng thái, không phải hai: `BookingStatusBadge` đã gộp sẵn bước
 * của tài xế vào nhãn ("Tài xế đã nhận" · "Đang đi"), nên dán thêm
 * `DriverStatusBadge` cạnh nó là in lại đúng một điều hai lần.
 */
export function MyTripCard({ trip }: { trip: VehicleBooking }) {
  const isDelivery = trip.request_type === REQUEST_TYPE.delivery
  const TypeIcon = isDelivery ? DeliveryBookingIcon : CarBookingIcon

  return (
    //  `h-full` + cột dọc: mọi thẻ trên một hàng cao bằng nhau và cụm nút luôn
    //  dính đáy (`mt-auto`), dù mục đích dài ngắn khác nhau.
    <article className="group relative flex h-full flex-col rounded-xl border bg-card shadow-xs transition-colors hover:border-primary/40 hover:bg-accent/30">
      {/*  Cả thẻ mở chi tiết, làm bằng LIÊN KẾT PHỦ chứ không bọc `role="button"`
          quanh nội dung: bọc như vậy là nút-lồng-trong-nút (cụm thao tác bên dưới
          cũng là `<button>`), trình đọc màn hình đọc ra một khối không rõ bấm được
          cái gì. Cụm nút nâng lên `z-10` để nằm trên lớp phủ này. */}
      <Link
        to={appRoutes.vehicleBooking.detail(trip.id)}
        className="absolute inset-0 rounded-xl focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
        aria-label={`Xem chi tiết chuyến ${trip.code}`}
      />

      <div className="flex flex-col gap-3 p-4">
        {/* --- Hàng phụ: loại + mã phiếu · trạng thái --- */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex min-w-0 items-center gap-1.5 text-xs text-muted-foreground">
            <TypeIcon className="size-4 shrink-0" />
            <span className="truncate" title={trip.request_type_label}>
              {trip.request_type_label}
            </span>
            <span aria-hidden="true">·</span>
            <span className="shrink-0 font-medium tabular-nums text-foreground/70">{trip.code}</span>
          </div>
          <BookingStatusBadge status={trip.status} driverStatus={trip.driver_status} />
        </div>

        {/* --- Mục đích: thứ nhận ra chuyến, nên là tiêu đề --- */}
        <h3 className="line-clamp-2 text-[15px] font-semibold leading-snug text-foreground">
          {trip.purpose || trip.request_type_label}
        </h3>

        {/* --- Thời gian --- */}
        <div className="flex items-center gap-1.5 text-xs font-medium text-foreground/80">
          <Clock className="size-3.5 shrink-0 text-muted-foreground" />
          <span className="tabular-nums">{formatTripTime(trip.start_time, trip.end_time)}</span>
        </div>

        <TripRoute from={trip.start_location} to={trip.end_location} />

        {/* --- Xe + một chi tiết theo loại chuyến --- */}
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
          <span className="inline-flex min-w-0 items-center gap-1.5">
            <TypeIcon className="size-3.5 shrink-0" />
            {/*  Tự lái thì KHÔNG có tài xế được phân — nói thẳng ra, đừng để trống,
                vì ô trống ở đây đọc ra là "chưa bố trí xe". */}
            <span className="truncate">
              {trip.assigned_vehicle_label || (trip.is_self_drive ? 'Tự lái' : 'Chưa bố trí xe')}
            </span>
          </span>
          {isDelivery
            ? trip.goods_name && (
                <span className="inline-flex min-w-0 items-center gap-1.5">
                  <Package className="size-3.5 shrink-0" />
                  <span className="truncate">{trip.goods_name}</span>
                </span>
              )
            : trip.passenger_count > 0 && (
                <span className="inline-flex shrink-0 items-center gap-1.5">
                  <Users className="size-3.5" />
                  {trip.passenger_count} khách
                </span>
              )}
        </div>
      </div>

      {/* --- Cụm nút: chỉ việc của TÀI XẾ (xem prop `scope`) --- */}
      <div className="relative z-10 mt-auto flex flex-wrap items-center gap-2 border-t px-4 py-3">
        <BookingWorkflowActions booking={trip} scope="driver" onDispatch={() => undefined} />
      </div>
    </article>
  )
}

/**
 * Lộ trình đi → đến, vẽ như một trục nhỏ: chấm rỗng ở điểm đi, chấm đặc ở điểm
 * đến, một nét nối giữa hai chấm.
 *
 * Mỗi địa điểm gói đúng MỘT dòng (`truncate`, địa chỉ đủ nằm ở `title` và ở trang
 * chi tiết). Cho xuống dòng thì hai ô chữ cao khác nhau và chấm thứ hai trôi khỏi
 * dòng chữ của nó — trục gãy, đọc ra hai chấm rời rạc chứ không ra một lộ trình.
 */
function TripRoute({ from, to }: { from: string; to: string }) {
  return (
    <div className="flex gap-2.5">
      {/*  `py-[7px]` đưa tâm mỗi chấm về đúng tâm dòng chữ ngang nó (dòng cao 16px,
          chấm 6px → chừa 5px… cộng 2px căn thị giác). */}
      <div className="flex flex-col items-center py-[7px]">
        <Dot />
        {/*  `bg-border` (#e2e8f0) mảnh 1px dài 14px thì gần như tàng hình trên nền
            thẻ trắng — đo xong soi lại ảnh vẫn không thấy nét nào. Đậm hơn một bậc
            để hai chấm đọc ra MỘT trục, không ra hai dấu rời. */}
        <span className="my-1 w-px flex-1 bg-muted-foreground/30" />
        <Dot solid />
      </div>
      <div className="flex min-w-0 flex-1 flex-col gap-2 text-sm">
        <span className="truncate text-muted-foreground" title={from || undefined}>
          {from || '—'}
        </span>
        <span className="truncate text-foreground" title={to || undefined}>
          {to || '—'}
        </span>
      </div>
    </div>
  )
}

function Dot({ solid = false }: { solid?: boolean }) {
  return (
    <span
      className={cn(
        'size-1.5 shrink-0 rounded-full',
        solid ? 'bg-primary' : 'bg-transparent ring-1 ring-muted-foreground/50',
      )}
    />
  )
}
