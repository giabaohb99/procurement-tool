import { ArrowLeft, Clock, MapPin, User } from 'lucide-react'
import { useEffect, useRef } from 'react'
import type { ReactNode } from 'react'

import { Button } from '@/shared/ui/button'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/shared/ui/tooltip'

import { REQUEST_TYPE, type VehicleBooking } from '../types/vehicle-booking'
import { formatTripTime } from '../utils/format-trip-time'
import { CarBookingIcon, DeliveryBookingIcon } from './booking-type-icons'
import { BookingStatusBadge } from './status-pill'

/**
 * Tiêu đề trang CHI TIẾT phiếu đặt xe.
 *
 * Ba việc mà bản trước bỏ trống:
 *
 * 1. **Mã phiếu**. Trước chỉ có mục đích chuyến, mà mục đích thì trùng nhau
 *    hàng loạt ("Thăm khách hàng" có mấy chục phiếu). Mã mới là thứ đọc qua
 *    điện thoại và đối chiếu với giấy tờ — nó phải nằm ngay dưới mắt.
 * 2. **Tóm tắt chuyến** (thời gian · lộ trình · xe · người tạo). Trước phải cuộn
 *    xuống thân phiếu mới biết chuyến đi lúc nào, đi đâu — tức là mỗi lần mở
 *    phiếu để quyết định duyệt/điều phối đều phải cuộn.
 * 3. **Phân tách khỏi thân phiếu**: một đường kẻ dưới, để dải nút không lẫn vào
 *    ô dữ liệu ngay bên dưới.
 */
export function BookingDetailHeader({
  booking,
  onBack,
  actions,
}: {
  booking: VehicleBooking
  onBack: () => void
  /** Cụm nút thao tác — dồn phải, xuống hàng riêng ở khổ hẹp. */
  actions?: ReactNode
}) {
  const TypeIcon =
    booking.request_type === REQUEST_TYPE.delivery ? DeliveryBookingIcon : CarBookingIcon
  const route = [booking.start_location, booking.end_location].filter(Boolean).join(' → ')

  //  Báo CHIỀU CAO THẬT của tiêu đề ra ngoài, dưới dạng biến CSS trên thẻ cha, để
  //  cột phụ bên phải dính được ngay DƯỚI nó (`top: var(--booking-header-h)`).
  //
  //  Phải đo chứ không viết số cứng: tiêu đề cao 104px khi mục đích chuyến gói
  //  một dòng, 144px khi hai dòng, 176px ở khổ hẹp — ghim một con số thì nửa số
  //  phiếu sẽ có cột phụ chui xuống dưới tiêu đề hoặc hở một khoảng trắng.
  const ref = useRef<HTMLElement>(null)
  useEffect(() => {
    const el = ref.current
    const host = el?.parentElement
    if (!el || !host) return
    const observer = new ResizeObserver(() =>
      host.style.setProperty('--booking-header-h', `${el.offsetHeight}px`),
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  return (
    //  LƯỚI 2 cột chứ không phải flex lồng nhau:
    //
    //  · cột 1 = nút quay lại · cột 2 = mọi thứ còn lại;
    //  · hàng 1 = tiêu đề + cụm nút · hàng 2 = dải thông tin phụ.
    //
    //  `items-center` cho HÀNG 1 tự căn giữa: nút cao 36px xếp cạnh chữ thấp hơn,
    //  căn theo mép TRÊN (bản trước) thì tâm nút tụt xuống 9px so với tâm chữ —
    //  đủ để mắt đọc ra là lệch.
    //
    //  Lưới cũng làm tiêu đề thụt vào ĐÚNG bằng bề ngang nút + khe, tự tính; viết
    //  tay một `pl-12` thì đổi cỡ nút là lệch mà không ai nhận ra.
    //  DÍNH ĐỈNH khi cuộn. Phiếu đặt xe dài (thân phiếu + lộ trình + giao hàng +
    //  ghi chú), mà cụm nút quyết định lại nằm ở tiêu đề — không dính thì đọc tới
    //  cuối phiếu rồi phải cuộn ngược lên mới bấm được, và lúc đó mã phiếu cũng
    //  đã khuất nên không còn gì xác nhận đang đứng ở phiếu nào.
    //
    //  KHÔNG kẻ viền dưới: nội dung bên dưới là các thẻ nền TRẮNG trên nền canvas
    //  xám nhạt, tự nó đã tách khỏi tiêu đề. Thêm viền thì ngay dưới nó là mép
    //  trên của thẻ đầu tiên — hai đường kẻ cách nhau một khoảng hẹp.
    //
    //  Ba thứ phải đi kèm `sticky`, thiếu cái nào cũng lòi nội dung ra sau:
    //  · `bg-canvas` — nền ĐẶC, khớp nền của `<main>`; để trong suốt thì chữ bên
    //    dưới chạy xuyên qua tiêu đề.
    //  · `-mx-4 px-4` (và bản `lg:`) — kéo nền ra sát mép, bù đúng lề `p-4 lg:p-6`
    //    của `PageContainer`; không bù thì hai dải lề trái/phải vẫn hở.
    //  · `-mt-4 pt-4` — nuốt lề trên của container vào trong tiêu đề, nếu không
    //    thì khoảng lề đó cuộn qua phía sau và chữ dính sát mép trên.
    //
    //  CHỈ dính từ `lg` trở lên. Đo thật: khổ rộng tiêu đề cao ~100px (11% chiều
    //  cao vùng cuộn), nhưng khổ hẹp thì tiêu đề xuống hai dòng, cụm nút tụt
    //  xuống hàng riêng và dải tóm tắt gãy làm bốn — thành 176px, tức **18–21%
    //  màn hình** bị khoá vĩnh viễn. Trên điện thoại đó là cái giá quá đắt cho
    //  một dải nút; ở đó cuộn bình thường.
    <header
      ref={ref}
      className="static top-0 z-20 -mx-4 -mt-4 mb-4 grid grid-cols-[auto_minmax(0,1fr)] items-center gap-x-3 gap-y-2 bg-canvas px-4 pt-4 pb-3 lg:sticky lg:-mx-6 lg:-mt-6 lg:px-6 lg:pt-6"
    >
      <Button
        variant="outline"
        size="icon"
        className="shrink-0"
        aria-label="Về danh sách yêu cầu đặt xe"
        onClick={onBack}
      >
        <ArrowLeft className="size-4" />
      </Button>

      {/* Hàng 1, cột 2: TIÊU ĐỀ (trái) · cụm nút (phải) */}
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-x-4 gap-y-2">
        {/*  `line-clamp-2` chứ không `truncate`: mục đích chuyến hay là một câu dài
            ("Tự lái đi công tác miền Tây: làm việc với ba nhà cung cấp…"), cắt về
            một dòng thì mất phần nói rõ chuyến đi đâu làm gì. `min-w-0 flex-1` giữ
            cụm nút luôn sát mép phải kể cả khi tiêu đề xuống hai dòng. */}
        <h1 className="line-clamp-2 min-w-0 flex-1 text-xl font-semibold tracking-tight text-navy dark:text-foreground">
          {booking.purpose || `Yêu cầu đặt xe ${booking.code}`}
        </h1>
        {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
      </div>

      {/*  Hàng 2, cột 2: DẢI THÔNG TIN PHỤ — định danh phiếu rồi tới tóm tắt chuyến.
          Loại · mã · trạng thái nằm ở đây chứ không phải trên tiêu đề: chúng là
          thông tin tra cứu, cùng hạng với thời gian/lộ trình/xe, nên gom về một
          dải duy nhất để hàng đầu chỉ còn đúng hai thứ — phiếu này là gì, và làm
          gì với nó. */}
      <div className="col-start-2 flex min-w-0 flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
        <div className="flex shrink-0 items-center gap-2">
          <TypeIcon className="size-3.5 shrink-0" />
          <span>{booking.request_type_label}</span>
          <span aria-hidden="true">·</span>
          <span className="font-semibold text-foreground/80 tabular-nums">{booking.code}</span>
          <BookingStatusBadge status={booking.status} driverStatus={booking.driver_status} />
        </div>

        {/*  Tóm tắt chuyến. `flex-wrap` + `min-w-0` trên từng mục để lộ trình dài
              cắt bớt chứ không đẩy cả hàng tràn ra ngoài. */}
        <dl className="flex min-w-0 flex-wrap items-center gap-x-4 gap-y-1">
          <MetaItem icon={<Clock className="size-3.5" />} label="Thời gian">
            <span className="tabular-nums">
              {formatTripTime(booking.start_time, booking.end_time)}
            </span>
          </MetaItem>
          {route && (
            <MetaItem icon={<MapPin className="size-3.5" />} label="Lộ trình">
              {/*  Cắt TỪNG ĐẦU một, không cắt cả chuỗi "A → B": cắt cả chuỗi thì
                    địa chỉ đi (thường dài) ăn hết chỗ và ĐIỂM ĐẾN biến mất — đúng
                    nửa thông tin mà người đọc cần nhất. */}
              <span className="flex items-center gap-1">
                <TruncatedText text={booking.start_location} />
                <span aria-hidden="true">→</span>
                <TruncatedText text={booking.end_location} />
              </span>
            </MetaItem>
          )}
          <MetaItem icon={<TypeIcon className="size-3.5" />} label="Xe">
            {/*  Tự lái thì không có tài xế được phân — nói thẳng, vì ô trống ở đây
                  đọc ra là "chưa bố trí xe". */}
            {booking.assigned_vehicle_label ||
              (booking.is_self_drive ? 'Tự lái' : 'Chưa bố trí xe')}
          </MetaItem>
          {booking.requester && (
            <MetaItem icon={<User className="size-3.5" />} label="Người tạo">
              {booking.requester}
            </MetaItem>
          )}
        </dl>
      </div>
    </header>
  )
}

/**
 * Đoạn chữ bị cắt bớt, xem đủ bằng TOOLTIP.
 *
 * Không dùng `title` của HTML: trình duyệt chờ ~1 giây mới hiện, vẽ bằng dáng
 * của hệ điều hành (không theo giao diện), và trên thiết bị cảm ứng thì KHÔNG
 * hiện gì cả — tức là trên điện thoại địa chỉ bị cắt là mất hẳn.
 *
 * Tooltip mở cả khi TRỎ CHUỘT lẫn khi lia BÀN PHÍM tới, nên phần tử phải nhận
 * được tiêu điểm (`tabIndex={0}`).
 */
function TruncatedText({ text }: { text: string }) {
  if (!text) return <span>—</span>
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            tabIndex={0}
            className="max-w-[20ch] truncate rounded-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {text}
          </span>
        </TooltipTrigger>
        {/*  Chặn bề ngang + cho bẻ dòng: mặc định tooltip rộng theo nội dung, mà
            địa chỉ đầy đủ dài hơn cả màn hình thì khung tooltip tràn ra ngoài. */}
        <TooltipContent className="max-w-xs break-words">{text}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

/**
 * Một mục tóm tắt: icon + giá trị, nhãn chỉ dành cho trình đọc màn hình.
 *
 * Icon một mình thì người dùng bàn phím / trình đọc màn hình nghe ra một chuỗi
 * rời rạc không biết là cái gì — nên nhãn vẫn có trong DOM, chỉ ẩn khỏi mắt.
 */
function MetaItem({
  icon,
  label,
  children,
}: {
  icon: ReactNode
  label: string
  children: ReactNode
}) {
  return (
    <div className="flex min-w-0 items-center gap-1.5">
      <dt className="flex shrink-0 items-center gap-1.5">
        <span aria-hidden="true">{icon}</span>
        <span className="sr-only">{label}</span>
      </dt>
      <dd className="truncate">{children}</dd>
    </div>
  )
}
