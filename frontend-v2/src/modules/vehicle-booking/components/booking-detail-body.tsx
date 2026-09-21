import { REQUEST_TYPE, type VehicleBooking } from '../types/vehicle-booking'
import { BookingDeliveryCard } from './booking-delivery-card'
import { BookingRequesterCard } from './booking-requester-card'
import { BookingRouteCard } from './booking-route-card'

/**
 * Thân chi tiết phiếu đặt xe.
 *
 * Bố cục (đổi 19/09/2026): NGƯỜI YÊU CẦU → LỘ TRÌNH → (HÀNG HÓA) — ai đặt, rồi
 * mới tới đi đâu, chở gì. Cả mạch trả lời đúng một câu: *chuyến đi này là gì*.
 *
 * Hai thẻ CỐ Ý không nằm ở đây mà ở CỘT PHỤ bên phải (xem
 * `vehicle-booking-detail-page.tsx`) vì chúng trả lời câu khác — *phiếu đang ở
 * đâu, ai dặn gì* — và cần thấy được trong lúc đọc phần thân:
 * **Tiến trình xử lý**, và **Ghi chú** (dời sang đó 21/09/2026, xem
 * `BookingNoteCard`).
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
    </>
  )
}
