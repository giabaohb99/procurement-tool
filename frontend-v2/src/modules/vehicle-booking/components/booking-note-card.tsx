import { StickyNote } from 'lucide-react'

import { Card } from '@/shared/ui/card'
import type { VehicleBooking } from '../types/vehicle-booking'
import { BookingCardHeader } from './booking-info-item'

/**
 * Thẻ **GHI CHÚ** của phiếu đặt xe — đứng ở CỘT PHỤ bên phải (đổi 21/09/2026,
 * trước đó khép lại thân phiếu ở cột chính).
 *
 * Ghi chú là lời NGƯỜI LẬP dặn thêm, và người đọc nó là người sắp quyết định
 * (duyệt · điều phối · nhận chuyến) — nên nó thuộc về cột trả lời *phiếu đang ở
 * đâu, ai dặn gì*, cạnh Tiến trình và Luồng duyệt, chứ không nằm cuối mạch
 * *chuyến đi này là gì* (lộ trình → hàng hóa → người yêu cầu).
 *
 * Tách khỏi `BookingDetailBody` chứ không truyền cờ ẩn/hiện: thân phiếu và cột
 * phụ là hai chỗ gọi khác nhau, mà một thẻ thì chỉ nên có một chủ.
 */
export function BookingNoteCard({ booking }: { booking: VehicleBooking }) {
  //  Chỉ hiện khi ghi chú CÓ NỘI DUNG THẬT — `.trim()` để ô toàn khoảng trắng /
  //  xuống dòng cũng coi như rỗng, không dựng khung trống.
  if (!booking.note?.trim()) return null

  return (
    <Card className="flex flex-col gap-3 p-5 pb-4">
      <BookingCardHeader
        icon={<StickyNote className="size-5 text-amber-600 dark:text-amber-400" />}
      >
        Ghi chú
      </BookingCardHeader>
      {/*  `whitespace-pre-wrap` giữ nguyên xuống dòng người ta gõ; ở cột hẹp
          360px thì `break-words` lo phần địa chỉ / số điện thoại dài không có
          khoảng trắng — không có nó thì một chuỗi dài đẩy cả thẻ tràn ra ngoài. */}
      <p className="whitespace-pre-wrap break-words text-sm leading-relaxed text-foreground">
        {booking.note}
      </p>
    </Card>
  )
}
