import type { RefObject } from 'react'

import { columnWidthVar } from '../hooks/use-list-column-widths'
import { HEADER_HEIGHT } from '../utils/gantt-layout'
import { LEAD_WIDTH, ROW_PAD_LEFT } from '../utils/list-metrics'
import type { TaskListColumn } from '../utils/list-columns'
import { ListColumnResizer } from './list-column-resizer'
import { TaskGroupsBoard, type TaskGroupsBoardProps } from './task-groups-board'

interface GanttGridProps extends TaskGroupsBoardProps {
  titleColumn: TaskListColumn
  /** Khung bao có biến CSS bề rộng cột — tay cầm kéo giãn đo theo nó. */
  gridRef: RefObject<HTMLDivElement | null>
  /** Bề rộng ô chứa lưới; cột không lọt vào đây đã bị lọc từ trước. */
  paneWidth: number
  onResize: (key: string, width: number) => void
}

/**
 * LƯỚI TRÁI của Gantt — **chính là khung nhìn Danh sách**, đúng như Lark: cùng
 * bộ cột (`buildListColumns`), cùng ô sửa tại chỗ, và cùng ba tầng kéo thả
 * (việc · việc con · cột) nhờ dùng chung `TaskGroupsBoard`.
 *
 * Trước đây chỗ này tự vẽ một bộ dòng "chỉ xem" riêng: người dùng phải nhớ khung
 * nhìn nào sửa được khung nhìn nào không, không kéo thả được gì, và không có
 * dòng «Việc mới». Nay khác biệt duy nhất so với Danh sách là **mọi dòng cao
 * đúng `rowHeight`** — để mỗi dòng khớp một hàng của trục thời gian.
 *
 * Lưới này DÍNH khi cuộn ngang và nằm CHUNG một khung cuộn với trục thời gian
 * (xem `gantt-view.tsx`), nhờ vậy hai bên không bao giờ lệch hàng theo chiều
 * dọc — khỏi phải đồng bộ hai thanh cuộn bằng tay.
 */
export function GanttGrid({
  titleColumn,
  gridRef,
  paneWidth,
  onResize,
  ...boardProps
}: GanttGridProps) {
  return (
    <div
      ref={gridRef}
      /*  ⚠️ KHÔNG đặt `overflow-hidden` ở đây để cắt cột thừa: `overflow` khác
          `visible` biến ô này thành khung cuộn của riêng nó, và hàng tiêu đề
          `sticky top-0` bên trong sẽ dính vào MÉP CỦA Ô — tức không dính gì cả,
          vì ô không cuộn. Hệ quả đo được: cuộn xuống thì tiêu đề của lưới trái
          trôi mất trong khi tiêu đề trục thời gian vẫn đứng.

          Cột không vừa được LỌC TỪ TRƯỚC (xem `gantt-view.tsx`) nên chẳng còn gì
          phải cắt.  */
      className="shrink-0 bg-card"
      style={{ width: paneWidth }}
    >
      <div
        //  Nền ĐỤC, không phải `bg-muted/50`: hàng này dính lại khi cuộn nên các
        //  dòng việc chui ngay dưới nó — nền trong là chữ chồng lên chữ.
        className="group/head sticky top-0 z-10 flex items-end gap-1.5 border-b bg-muted pr-2 pb-2 text-xs font-medium text-muted-foreground"
        style={{ height: HEADER_HEIGHT, paddingLeft: ROW_PAD_LEFT }}
      >
        {/*  Ô tiêu đề cột TÊN thụt thêm đúng phần dẫn đầu của dòng việc (mũi tên
             bung + ô tick) để chữ «Tên công việc» thẳng hàng với tên việc bên
             dưới — cùng cách tính với khung nhìn Danh sách. */}
        <HeaderCell
          column={titleColumn}
          gridRef={gridRef}
          onResize={onResize}
          padLeft={LEAD_WIDTH}
        />
        <span className="min-w-0 flex-1" aria-hidden />
        {boardProps.columns.map((col) => (
          <HeaderCell key={col.key} column={col} gridRef={gridRef} onResize={onResize} />
        ))}
      </div>

      <TaskGroupsBoard {...boardProps} />
    </div>
  )
}

function HeaderCell({
  column,
  gridRef,
  onResize,
  padLeft,
}: {
  column: TaskListColumn
  gridRef: RefObject<HTMLDivElement | null>
  onResize: (key: string, width: number) => void
  padLeft?: number
}) {
  return (
    //  KHÔNG đặt `truncate` ở đây: nó kèm `overflow-hidden`, mà tay cầm kéo giãn
    //  nằm NGOÀI hộp nên bị cắt mất — nhìn như bảng không kéo giãn được.
    <span
      className="relative shrink-0"
      style={{ width: `var(${columnWidthVar(column.key)})`, paddingLeft: padLeft }}
    >
      <span className="block truncate">{column.label}</span>
      <ListColumnResizer
        columnKey={column.key}
        gridRef={gridRef}
        minWidth={column.minWidth}
        onResize={(width) => onResize(column.key, width)}
      />
    </span>
  )
}
