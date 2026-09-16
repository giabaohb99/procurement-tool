import { TriangleAlert } from 'lucide-react'

import { cn } from '@/shared/utils/cn'

import { BOOKING_STATUS_LABELS } from '../types/vehicle-booking'
import { CALENDAR_STATUS_STYLE } from '../utils/calendar-status-colors'

/**
 * Chú giải màu cho lịch đặt xe.
 *
 * Bắt buộc phải có: lịch mã hoá trạng thái BẰNG MÀU và có tới 8 mức — không ai
 * nhớ được 8 màu, nên thiếu hàng này thì màu không nói lên điều gì. Kèm luôn dấu
 * hiệu không phải màu (tam giác = chưa điều phối) vì nó cũng mang nghĩa.
 */
export function BookingCalendarLegend({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-muted-foreground',
        className,
      )}
    >
      {Object.entries(CALENDAR_STATUS_STYLE).map(([status, style]) => (
        <span key={status} className="flex items-center gap-1.5">
          <span
            className="size-2.5 shrink-0 rounded-[3px]"
            style={{ backgroundColor: style.color }}
          />
          {BOOKING_STATUS_LABELS[Number(status)]}
        </span>
      ))}

      {/*  Dấu hiệu KHÔNG phải màu — kẻ vạch ngăn cho khỏi lẫn vào dải màu trạng
           thái. Bỏ mục "chuyến nhiều ngày": mọi chip nay cùng nền đặc, chuyến
           nhiều ngày tự nhận ra vì trải ngang nhiều cột. */}
      <span className="flex items-center gap-1.5 border-l pl-3">
        <TriangleAlert className="size-3 shrink-0 text-amber-500" />
        Chưa điều phối
      </span>
    </div>
  )
}
