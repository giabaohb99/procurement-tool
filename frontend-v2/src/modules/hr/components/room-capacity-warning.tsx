import { AlertTriangle } from 'lucide-react'

import { cn } from '@/shared/utils/cn'

interface RoomCapacityWarningProps {
  /** Tên phòng đang chọn — nói đích danh, «phòng này» thì phải nhớ lại là phòng nào. */
  roomName: string
  capacity: number
  className?: string
}

/**
 * Câu cảnh báo VƯỢT SỨC CHỨA — dùng ở HAI chỗ, và cố ý chỉ một chỗ hiện ra tại
 * mỗi khổ màn hình.
 *
 * - Màn rộng: nằm ở cột phải (`RoomBookingSidePanel`) — cột đó dính khi cuộn nên
 *   cảnh báo còn trong tầm mắt lúc người dùng đang gõ ở dưới.
 * - Khổ hẹp: cột phải bị ẩn (nó chỉ lặp lại thứ vừa nhập, xem
 *   `room-booking-detail-page`), nên câu này phải mọc lại ngay dưới ô «Số người
 *   dự» — chỗ duy nhất sửa được lỗi đó.
 *
 * ⚠️ Tách thành một tệp chứ không chép câu chữ sang hai chỗ: đây là câu báo
 * trước một cú CHẶN THẬT ở backend, hai bản chép sẽ lệch nhau vào ngày ai đó
 * sửa luật sức chứa và chỉ tìm thấy một bản.
 */
export function RoomCapacityWarning({ roomName, capacity, className }: RoomCapacityWarningProps) {
  return (
    <p
      className={cn(
        'flex items-start gap-1.5 rounded-md border border-destructive/40 bg-destructive/10 p-2 text-xs text-destructive',
        className,
      )}
    >
      <AlertTriangle className="mt-px size-3.5 shrink-0" />
      <span>
        Vượt sức chứa của {roomName} ({capacity} chỗ). Phiếu sẽ bị chặn lúc lưu — chọn phòng
        lớn hơn hoặc sửa lại số người.
      </span>
    </p>
  )
}
