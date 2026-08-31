import { cn } from '@/shared/utils/cn'
import { HEADER_HEIGHT, ROW_HEIGHT } from '../utils/gantt-layout'
import type { GanttHeader, GanttZoom } from '../utils/gantt-scale'

interface GanttTimelineHeaderProps {
  header: GanttHeader
  zoom: GanttZoom
}

/**
 * Hai hàng tiêu đề của trục thời gian — hàng trên gom (tháng / năm), hàng dưới
 * là ô đọc được (ngày · tuần `T.37` · tháng `Th 9`). Nội dung do
 * `buildHeader` quyết định, ở đây chỉ còn việc vẽ.
 *
 * `sticky top-0`: cuộn dọc một dự án dài mà mất hàng tiêu đề thì mọi thanh đều
 * thành "một thanh nằm đâu đó", không đọc ra ngày nào nữa.
 */
export function GanttTimelineHeader({ header, zoom }: GanttTimelineHeaderProps) {
  return (
    //  Nền ĐỤC: thanh và mũi tên trôi ngay dưới hàng này khi cuộn dọc, nền trong
    //  là chúng hiện xuyên qua chữ ngày tháng.
    <div className="sticky top-0 z-20 bg-muted" style={{ height: HEADER_HEIGHT }}>
      <div className="flex" style={{ height: ROW_HEIGHT }}>
        {header.top.map((cell) => (
          <div
            key={cell.key}
            style={{ width: cell.width }}
            className="flex shrink-0 items-center justify-center border-r border-b text-xs font-medium text-muted-foreground"
          >
            {/*  Ô hẹp hơn chữ thì thà bỏ trống: chữ tràn ra sẽ đè lên ô bên
                 cạnh và cả hàng thành một dải chữ chồng nhau không đọc nổi. */}
            <span className="truncate px-1">{cell.width >= 56 ? cell.label : ''}</span>
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
              zoom === 'day' ? 'text-[10px]' : 'text-[11px]',
              cell.isNow
                ? 'bg-primary/10 font-semibold text-primary'
                : 'text-muted-foreground',
            )}
          >
            <span className="truncate">{cell.width >= 22 ? cell.label : ''}</span>
            {cell.sub && <span className="mt-0.5 opacity-70">{cell.sub}</span>}
          </div>
        ))}
      </div>
    </div>
  )
}
