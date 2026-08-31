import { cn } from '@/shared/utils/cn'
import { HEADER_HEIGHT, ROW_HEIGHT } from '../utils/gantt-layout'
import type { GanttHeader, GanttZoom } from '../utils/gantt-scale'

interface GanttTimelineHeaderProps {
  header: GanttHeader
  zoom: GanttZoom
}

/**
 * Hai hàng tiêu đề của trục thời gian, đúng lối Lark: **hàng trên là THÁNG (hay
 * năm), hàng dưới là NGÀY** (hoặc tuần `T.37` / tháng `Th 9`, tùy mức phóng).
 * Nội dung do `buildHeader` quyết định, ở đây chỉ còn việc vẽ.
 *
 * **Nhãn hàng trên DÍNH khi cuộn ngang** (`sticky left-0`, mốc là mép trái của
 * chính khung cuộn trục thời gian — trục nay là khung cuộn riêng, xem
 * `gantt-view.tsx`): kéo sang giữa tháng 9 mà
 * chữ "Tháng 9/2026" đã trôi khỏi màn hình thì người dùng chỉ còn nhìn thấy một
 * dãy số 1…30 không biết của tháng nào. Sticky đặt trên chính ô của tháng ấy nên
 * nhãn chỉ trượt trong lòng tháng mình rồi nhường chỗ cho tháng kế — không bao
 * giờ có hai nhãn chồng nhau.
 *
 * `sticky top-0` thì lo chiều dọc: cuộn xuống một dự án dài mà mất hàng tiêu đề
 * thì mọi thanh đều thành "một thanh nằm đâu đó", không đọc ra ngày nào nữa.
 */
export function GanttTimelineHeader({ header, zoom }: GanttTimelineHeaderProps) {
  return (
    <div className="sticky top-0 z-20 bg-muted" style={{ height: HEADER_HEIGHT }}>
      <div className="flex" style={{ height: ROW_HEIGHT }}>
        {header.top.map((cell) => (
          <div
            key={cell.key}
            style={{ width: cell.width }}
            className="relative shrink-0 border-r border-b"
          >
            {/*  Ô hẹp hơn chữ thì thà bỏ trống: chữ tràn ra sẽ đè lên ô bên
                 cạnh và cả hàng thành một dải chữ chồng nhau không đọc nổi. */}
            {cell.width >= 56 && (
              <span
                className="sticky left-0 inline-block truncate px-3 py-3 text-sm font-medium"
                style={{ maxWidth: cell.width }}
              >
                {cell.label}
              </span>
            )}
          </div>
        ))}
      </div>

      <div className="flex" style={{ height: ROW_HEIGHT }}>
        {header.bottom.map((cell) => (
          <div
            key={cell.key}
            style={{ width: cell.width }}
            className={cn(
              'flex shrink-0 flex-col items-center justify-center border-r border-b leading-none',
              zoom === 'day' ? 'text-[11px]' : 'text-[12px]',
              cell.isNow
                ? 'bg-primary/10 font-semibold text-primary'
                : 'text-muted-foreground',
            )}
          >
            <span className="truncate">{cell.width >= 22 ? cell.label : ''}</span>
            {cell.sub && <span className="mt-1 text-[10px] opacity-70">{cell.sub}</span>}
          </div>
        ))}
      </div>
    </div>
  )
}
