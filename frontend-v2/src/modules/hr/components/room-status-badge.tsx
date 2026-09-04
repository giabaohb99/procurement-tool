import { Badge } from '@/shared/ui/badge'
import { cn } from '@/shared/utils/cn'
import { ROOM_BOOKING_STATUS, ROOM_BOOKING_STATUS_LABELS } from '../types/room'

/**
 * Huy hiệu trạng thái phiếu đặt phòng.
 *
 * ⚠️ **Không dùng màu `primary`** cho bất kỳ trạng thái nào: primary là màu nút
 * hành động chính, nên một huy hiệu primary đọc ra như thứ bấm được. Mỗi trạng
 * thái một họ màu riêng, và ba trạng thái "không thành" (từ chối · trả về ·
 * hủy) phải phân biệt được với nhau — chúng dẫn tới ba việc khác nhau: đặt
 * phiếu mới, sửa rồi gửi lại, hoặc không làm gì cả.
 */
const TONES: Record<number, string> = {
  [ROOM_BOOKING_STATUS.DRAFT]:
    'border-slate-300 bg-slate-100 text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300',
  [ROOM_BOOKING_STATUS.PENDING]:
    'border-amber-300 bg-amber-100 text-amber-800 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-200',
  [ROOM_BOOKING_STATUS.APPROVED]:
    'border-emerald-300 bg-emerald-100 text-emerald-800 dark:border-emerald-700 dark:bg-emerald-950 dark:text-emerald-200',
  [ROOM_BOOKING_STATUS.REJECTED]:
    'border-red-300 bg-red-100 text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200',
  [ROOM_BOOKING_STATUS.RETURNED]:
    'border-orange-300 bg-orange-100 text-orange-800 dark:border-orange-700 dark:bg-orange-950 dark:text-orange-200',
  [ROOM_BOOKING_STATUS.CANCELLED]:
    'border-zinc-300 bg-zinc-100 text-zinc-600 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-400',
}

interface RoomStatusBadgeProps {
  status: number
  /** Nhãn từ backend. Thiếu thì rơi về bảng nhãn gõ tay ở `types/room.ts`. */
  label?: string
  className?: string
}

export function RoomStatusBadge({ status, label, className }: RoomStatusBadgeProps) {
  return (
    <Badge
      variant="outline"
      className={cn(TONES[status] ?? TONES[ROOM_BOOKING_STATUS.DRAFT], className)}
    >
      {label || ROOM_BOOKING_STATUS_LABELS[status] || '—'}
    </Badge>
  )
}
