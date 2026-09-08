import type { RefObject } from 'react'

import { cn } from '@/shared/utils/cn'
import { columnWidthVar } from '../hooks/use-list-column-widths'
import { HEADER_HEIGHT } from '../utils/gantt-layout'
import { COLUMN_GAP, LEAD_WIDTH, ROW_PAD_LEFT } from '../utils/list-metrics'
import type { TaskListColumn } from '../utils/list-columns'
import { PINNED_TITLE_CELL } from '../utils/pinned-title-class'
import { ListColumnResizer } from './list-column-resizer'
import { TaskGroupsBoard, type TaskGroupsBoardProps } from './task-groups-board'

interface GanttGridProps extends TaskGroupsBoardProps {
  titleColumn: TaskListColumn
  /** Khung bao có biến CSS bề rộng cột — tay cầm kéo giãn đo theo nó. */
  gridRef: RefObject<HTMLDivElement | null>
  /** Bề rộng NỘI DUNG (mọi cột) — rộng hơn ô chứa thì lưới tự cuộn ngang. */
  contentWidth: number
  onResize: (key: string, width: number) => void
}

/**
 * LƯỚI TRÁI của Gantt — **chính là khung nhìn Danh sách**, đúng như Lark: cùng
 * bộ cột (`buildListColumns`, tức bộ «Tùy chỉnh»), cùng ô sửa tại chỗ, và cùng
 * ba tầng kéo thả (việc · việc con · cột) nhờ dùng chung `TaskGroupsBoard`.
 *
 * Lưới vẽ ĐỦ cột, còn ô chứa nó thì hẹp (mặc định vừa ~3 cột) — nên nó **tự
 * cuộn ngang**, và **ô TÊN ghim lại** ở mép trái (`stickyTitle`). Đây là chỗ
 * khác duy nhất so với Danh sách, cộng thêm việc mọi dòng cao đúng `rowHeight`
 * để khớp từng hàng của trục thời gian.
 *
 * ⚠️ Hàng tiêu đề `sticky top-0` chỉ dính được vì **chính ô chứa lưới là khung
 * cuộn** (`gantt-view.tsx` cho nó `overflow-x-auto`): sticky bám khung cuộn gần
 * nhất, mà khung ấy giờ là nó. Trước đây lưới không có `overflow` nên tiêu đề
 * bám khung cuộn CHUNG ở ngoài — hễ ai thêm `overflow` vào giữa là tiêu đề rơi.
 */
export function GanttGrid({
  titleColumn,
  gridRef,
  contentWidth,
  onResize,
  ...boardProps
}: GanttGridProps) {
  return (
    <div ref={gridRef} style={{ width: contentWidth }}>
      <div
        //  Nền ĐỤC: hàng này dính lại khi cuộn nên các dòng việc chui ngay dưới
        //  nó — nền trong là chữ chồng lên chữ.
        className="group/head sticky top-0 z-20 flex items-end border-b bg-muted pr-2 pb-2 text-xs font-medium text-muted-foreground"
        //  Khe LẤY TỪ HẰNG chứ không gõ lớp `gap-*`: hàng này phải khớp từng
        //  pixel với dòng việc bên dưới, mà hai bên từng lệch nhau đúng vì mỗi
        //  bên gõ một lớp khác nhau (xem `COLUMN_GAP`).
        style={{ height: HEADER_HEIGHT, paddingLeft: ROW_PAD_LEFT, gap: COLUMN_GAP }}
      >

        {/*  Ô tiêu đề cột TÊN cũng ghim trái như ô tên của từng dòng, và thụt
             thêm đúng phần dẫn đầu của dòng (mũi tên bung + ô tick) để chữ
             «Tên công việc» thẳng hàng với tên việc bên dưới. */}
        <HeaderCell
          column={titleColumn}
          gridRef={gridRef}
          onResize={onResize}
          padLeft={LEAD_WIDTH}
          sticky
        />

        {/*  Khoảng đệm nuốt phần dư — dòng việc có nó (`TaskListRow`), hàng này
             THIẾU nó nên mọi nhãn cột lệch sang trái đúng một khe. */}
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
  sticky,
}: {
  column: TaskListColumn
  gridRef: RefObject<HTMLDivElement | null>
  onResize: (key: string, width: number) => void
  padLeft?: number
  sticky?: boolean
}) {
  return (
    //  KHÔNG đặt `truncate` ở đây: nó kèm `overflow-hidden`, mà tay cầm kéo giãn
    //  nằm NGOÀI hộp nên bị cắt mất — nhìn như bảng không kéo giãn được.
    <span
      className={cn('shrink-0', sticky ? cn(PINNED_TITLE_CELL, 'bg-muted') : 'relative')}
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
