import { StickyNote } from 'lucide-react'

import { Card } from '@/shared/ui/card'
import { REQUEST_TYPE, type VehicleBooking } from '../types/vehicle-booking'
import { BookingDeliveryCard } from './booking-delivery-card'
import { BookingCardHeader } from './booking-info-item'
import { BookingRequesterCard } from './booking-requester-card'
import { BookingRouteCard } from './booking-route-card'

/**
 * Thân chi tiết phiếu đặt xe.
 *
 * Bố cục (đổi 19/09/2026): NGƯỜI YÊU CẦU → LỘ TRÌNH → (HÀNG HÓA) → GHI CHÚ —
 * ai đặt, rồi mới tới đi đâu, chở gì.
 * Thẻ **Tiến trình xử lý** không nằm ở đây mà ở CỘT PHỤ bên phải (xem
 * `vehicle-booking-detail-page.tsx`): nó là *phiếu đang ở đâu*, cùng loại với
 * luồng duyệt · trao đổi · lịch sử, và cần thấy được trong lúc đọc phần thân.
 *
 * Bản trước là bốn thẻ chứa ~24 ô có viền xếp thành lưới hai cột — trang XEM mà
 * nhìn ra một biểu mẫu bị khóa, và quá nửa số ô rỗng (chưa duyệt, chưa điều
 * phối, chưa chạy) nên mắt phải quét hết mới lọc ra được chỗ có chữ. Ba thay đổi:
 *
 * 1. **Bỏ ô có viền ở màn xem** — nhãn nhỏ + chữ trần (`BookingInfoItem`), giống
 *    chi tiết Văn thư. Chữ trần vẫn bôi đen / chép được, tức vẫn giữ đúng lý do
 *    ra đời của `ReadOnlyValue`.
 * 2. **Ô rỗng biến thành câu** — mười ô duyệt/điều phối/hoàn thành gom về một
 *    trục tiến trình, chặng chưa tới lượt đọc ra "Chờ điều phối".
 * 3. **Xếp theo việc, không theo bảng dữ liệu** — lộ trình vẽ thành đường đi,
 *    liên hệ đứng cạnh nút chép.
 *
 * Mục đích chuyến và loại phiếu KHÔNG lặp lại ở đây: chúng là tiêu đề trang
 * (`BookingDetailHeader`), bày thêm lần nữa chỉ làm dài phiếu.
 */
export function BookingDetailBody({ booking }: { booking: VehicleBooking }) {
  const isDelivery = booking.request_type === REQUEST_TYPE.delivery

  return (
    <>
      <BookingRequesterCard booking={booking} />
      <BookingRouteCard booking={booking} />
      {isDelivery && <BookingDeliveryCard booking={booking} />}

      {/*  Chỉ hiện khi ghi chú CÓ NỘI DUNG THẬT — `.trim()` để ô toàn khoảng trắng /
          xuống dòng cũng coi như rỗng, không dựng khung trống. */}
      {booking.note?.trim() && (
        <Card className="flex flex-col gap-3 p-5 pb-4">
          <BookingCardHeader icon={<StickyNote className="size-5 text-amber-600 dark:text-amber-400" />}>
            Ghi chú
          </BookingCardHeader>
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">{booking.note}</p>
        </Card>
      )}
    </>
  )
}
