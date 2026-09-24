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

      {/*  `flex-1` để hàng XE + hàng hàng hóa tụt xuống đáy phần nội dung
          (`mt-auto` bên dưới). Thẻ trong một lưới luôn cao bằng thẻ dài nhất
          hàng, nên thẻ ngắn thừa ra một khoảng trắng — để khoảng trắng đó nằm
          GIỮA lộ trình và dòng xe thì thẻ vẫn đọc ra ba tầng (việc · lộ trình ·
          phương tiện); để nó nằm ngay trên dải nút thì thẻ trông như bị hụt. */}
      <div className="flex flex-1 flex-col gap-3 p-4">
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
        <div className="mt-auto flex flex-wrap items-center gap-x-3 gap-y-1 pt-1 text-xs text-muted-foreground">
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

      {/*  --- Cụm nút: chỉ việc của TÀI XẾ (xem prop `scope`) ---
          ⚠️ `size="sm"` + `flex-1` cho từng nút là BẮT BUỘC ở đây, không phải cho
          đẹp: lưới ba cột chừa cho thẻ 285px, mà hai nút cỡ thường («Chấp nhận» +
          «Từ chối chuyến») cần 286px — nút thứ hai bị xén mất đuôi ngay trong
          viền thẻ. Chia đều bề ngang thì hai nút luôn vừa, và một nút đứng lẻ
          («Bắt đầu», «Hoàn thành») giãn hết hàng thành một vệt bấm rộng. */}
      <div className="relative z-10 mt-auto flex items-center gap-2 border-t px-4 py-3 [&>button]:min-w-0 [&>button]:flex-1">
        <BookingWorkflowActions
          booking={trip}
          scope="driver"
          size="sm"
          onDispatch={() => undefined}
        />
      </div>
    </article>
  )
}

/**
 * Lộ trình đi → đến, vẽ như một trục nhỏ: chấm rỗng ở điểm đi, chấm đặc ở điểm
 * đến, một nét nối giữa hai chấm.
 *
 * ⚠️ Mỗi địa điểm được phép xuống DÒNG THỨ HAI (`line-clamp-2`) chứ không cắt
 * cụt ở một dòng. Địa chỉ ở đây có dạng «Tên chỗ — số nhà, phường, quận, thành
 * phố», mà cắt một dòng thì phần rụng đi luôn là QUẬN/THÀNH PHỐ — đúng phần tài
 * xế cần để biết đi hướng nào («45 Đường số 8, P.Linh Trung, TP.Thủ Đức, TP.Hồ
 * Chí ...»). Hai dòng đủ cho phần lớn địa chỉ đang có.
 *
 * Chấm vì thế phải neo theo DÒNG ĐẦU của mỗi địa điểm (`mt-[7px]`), không neo
 * theo tâm khối chữ: địa điểm một dòng đứng cạnh địa điểm hai dòng mà neo giữa
 * thì hai chấm lệch nhau, trục gãy và đọc ra hai dấu rời rạc.
 */
function TripRoute({ from, to }: { from: string; to: string }) {
  return (
    <div className="grid grid-cols-[10px_minmax(0,1fr)] gap-x-2 text-sm">
      <TripStopDot />
      <span className="line-clamp-2 pb-2 text-muted-foreground" title={from || undefined}>
        {from || '—'}
      </span>

      <TripStopDot solid />
      <span className="line-clamp-2 text-foreground" title={to || undefined}>
        {to || '—'}
      </span>
    </div>
  )
}

/**
 * Chấm của một điểm dừng, kèm nét nối chạy xuống điểm kế tiếp.
 *
 * Nét nối vẽ bằng lớp phủ tuyệt đối chạy từ dưới chấm tới hết ô lưới, nên nó dài
 * ngắn theo chính đoạn chữ bên cạnh — địa chỉ xuống hai dòng thì trục dài theo,
 * không phải canh tay lại. Điểm ĐẾN (`solid`) không có nét nối vì không còn
 * chặng nào sau nó.
 *
 * ⚠️ `bg-border` (#e2e8f0) mảnh 1px thì gần như tàng hình trên nền thẻ trắng —
 * đo xong soi lại ảnh vẫn không thấy nét nào. Đậm hơn một bậc để hai chấm đọc ra
 * MỘT trục, không ra hai dấu rời.
 */
function TripStopDot({ solid = false }: { solid?: boolean }) {
  return (
    <div className="relative flex justify-center">
      <span
        className={cn(
          'mt-[7px] size-1.5 shrink-0 rounded-full',
          solid ? 'bg-primary' : 'bg-transparent ring-1 ring-muted-foreground/50',
        )}
      />
      {!solid && (
        <span className="absolute top-[15px] bottom-0.5 left-1/2 w-px -translate-x-1/2 bg-muted-foreground/30" />
      )}
    </div>
  )
}
