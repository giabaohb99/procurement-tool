import { Check, X } from 'lucide-react'
import type { ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'

/**
 * Một dòng trên trục dọc (lộ trình, tiến trình xử lý): ĐIỂM ĐÁNH DẤU bên trái,
 * nội dung bên phải, đường nối chạy từ điểm đánh dấu xuống dòng kế.
 *
 * Đường nối là một `<span>` GIÃN theo chiều cao dòng (`flex-1`) chứ không phải
 * viền trái có chiều cao cố định: nội dung mỗi chặng dài ngắn khác nhau (một
 * điểm dừng có thêm người liên hệ + ghi chú), viết số cứng thì chỗ đứt chỗ thừa.
 *
 * Đặt trong `<ol className="flex flex-col">`.
 *
 * Ở `shared/` vì đang dùng ở hai phân hệ (Đặt xe: lộ trình + tiến trình; Duyệt
 * dấu: tiến trình duyệt & đóng dấu) — dời lên 22/09/2026, trước đó nằm trong
 * `vehicle-booking/components/booking-timeline-item.tsx`.
 */
export function TimelineItem({
  marker,
  last,
  children,
}: {
  marker: ReactNode
  /** Dòng cuối: không vẽ đường nối, không chừa khoảng dưới. */
  last?: boolean
  children: ReactNode
}) {
  return (
    <li className="flex gap-3">
      <div className="flex flex-col items-center">
        {marker}
        {!last && <span className="w-px flex-1 bg-border" />}
      </div>
      <div className={cn('min-w-0 flex-1', last ? 'pb-0' : 'pb-4')}>{children}</div>
    </li>
  )
}

/**
 * Trạng thái một chặng xử lý:
 * · `done` — đã xảy ra · `pending` — chưa tới lượt · `stopped` — phiếu dừng ở đây.
 */
export type TimelineState = 'done' | 'pending' | 'stopped'

/** Vòng tròn đầu chặng: xong (đặc, dấu tick) · chờ (nét đứt) · dừng (đỏ, dấu X). */
export function TimelineMarker({ state }: { state: TimelineState }) {
  if (state === 'done') {
    return (
      <span className="grid size-5 shrink-0 place-items-center rounded-full bg-emerald-500 text-white">
        <Check className="size-3" strokeWidth={3} />
      </span>
    )
  }
  if (state === 'stopped') {
    return (
      <span className="grid size-5 shrink-0 place-items-center rounded-full bg-destructive text-white">
        <X className="size-3" strokeWidth={3} />
      </span>
    )
  }
  return (
    <span
      className="size-5 shrink-0 rounded-full border-2 border-dashed border-muted-foreground/40"
      aria-hidden="true"
    />
  )
}
