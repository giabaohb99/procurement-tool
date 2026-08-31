import { ChevronRight, Diamond } from 'lucide-react'
import type { RefObject } from 'react'

import { cn } from '@/shared/utils/cn'
import { columnWidthVar } from '../hooks/use-list-column-widths'
import type { WorkLabelField, WorkMember } from '../types/work'
import { WORK_TASK_STATUS } from '../types/work'
import { GRID_INDENT, GRID_PAD_LEFT, HEADER_HEIGHT, ROW_HEIGHT } from '../utils/gantt-layout'
import type { GanttRowItem } from '../utils/gantt-rows'
import { isMilestone } from '../utils/gantt-scale'
import type { TaskListColumn } from '../utils/list-columns'
import { chipClass } from '../utils/work-colors'
import { ListColumnResizer } from './list-column-resizer'
import { TaskListCell } from './task-list-row'
import type { GanttRowActions } from './gantt-view'

interface GanttGridProps extends GanttRowActions {
  rows: GanttRowItem[]
  columns: TaskListColumn[]
  titleColumn: TaskListColumn
  labelFields: WorkLabelField[]
  members: WorkMember[]
  canEdit: boolean
  /** Khung bao có biến CSS bề rộng cột — tay cầm kéo giãn đo theo nó. */
  gridRef: RefObject<HTMLDivElement | null>
  /** Bề rộng ô chứa lưới; cột vượt quá bị cắt, kéo thanh chia để xem thêm. */
  paneWidth: number
  onResize: (key: string, width: number) => void
  onToggleGroup: (key: string) => void
}

/**
 * LƯỚI TRÁI của Gantt: cùng bộ cột với khung nhìn Danh sách (`buildListColumns`),
 * nên tắt một trường ở menu «Tùy chỉnh» là nó biến khỏi cả ba khung nhìn.
 *
 * Ô dữ liệu dùng thẳng `TaskListCell` của dòng danh sách — sửa được tại chỗ y
 * hệt bên đó. Vẽ riêng một bộ ô "chỉ xem" cho Gantt thì người dùng phải nhớ
 * khung nhìn nào sửa được khung nhìn nào không, và mỗi kiểu trường mới lại phải
 * làm hai lần.
 *
 * Lưới này DÍNH khi cuộn ngang (`sticky left-0`) và nằm CHUNG một khung cuộn với
 * trục thời gian — nhờ vậy hai bên không bao giờ lệch hàng, khỏi phải đồng bộ
 * hai thanh cuộn dọc bằng tay.
 */
export function GanttGrid({
  rows,
  columns,
  titleColumn,
  labelFields,
  members,
  canEdit,
  gridRef,
  paneWidth,
  onResize,
  onToggleGroup,
  onOpenTask,
  onSetAssignees,
  onSetDue,
  onSetStart,
  onSetStatus,
  onSetLabel,
}: GanttGridProps) {
  return (
    <div
      ref={gridRef}
      /*  ⚠️ KHÔNG đặt `overflow-hidden` ở đây để cắt cột thừa: `overflow` khác
          `visible` biến ô này thành khung cuộn của riêng nó, và hàng tiêu đề
          `sticky top-0` bên trong sẽ dính vào MÉP CỦA Ô — tức không dính gì cả,
          vì ô không cuộn. Hệ quả đo được: cuộn xuống thì tiêu đề của lưới trái
          trôi mất trong khi tiêu đề trục thời gian vẫn đứng.

          Cột không vừa được LỌC TỪ TRƯỚC (`columns` chỉ gồm cột lọt vào ô, xem
          `gantt-view.tsx`) nên chẳng còn gì phải cắt.  */
      className="shrink-0 bg-card"
      style={{ width: paneWidth }}
    >
      <div
        //  Nền ĐỤC, không phải `bg-muted/50`: hàng này dính lại khi cuộn nên các
        //  dòng việc chui ngay dưới nó — nền trong là chữ chồng lên chữ.
        className="group/head sticky top-0 z-10 flex items-end gap-1.5 border-b bg-muted pr-2 pb-2 text-xs font-medium text-muted-foreground"
        style={{ height: HEADER_HEIGHT, paddingLeft: GRID_PAD_LEFT }}
      >
        <HeaderCell column={titleColumn} gridRef={gridRef} onResize={onResize} />
        {columns.map((col) => (
          <HeaderCell key={col.key} column={col} gridRef={gridRef} onResize={onResize} />
        ))}
      </div>

      {rows.map((row) =>
        row.kind === 'group' ? (
          <div
            key={row.key}
            style={{ height: ROW_HEIGHT, paddingLeft: GRID_PAD_LEFT }}
            className="flex items-center gap-1.5 border-b bg-muted/30 pr-2"
          >
            <button
              type="button"
              aria-expanded={!row.collapsed}
              aria-label={row.collapsed ? `Bung nhóm ${row.group.name}` : `Thu nhóm ${row.group.name}`}
              onClick={() => onToggleGroup(row.group.key)}
              className="flex min-w-0 items-center gap-1 rounded px-0.5 text-left text-sm font-medium hover:bg-accent"
            >
              <ChevronRight
                className={cn(
                  'size-3.5 shrink-0 text-muted-foreground transition-transform',
                  !row.collapsed && 'rotate-90',
                )}
              />
              <span
                className={cn(
                  'shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold tracking-wide uppercase',
                  chipClass(row.group.color || 'slate'),
                )}
              >
                Nhóm
              </span>
              <span className="truncate">{row.group.name}</span>
            </button>
            <span className="shrink-0 text-xs text-muted-foreground">
              {row.group.tasks.length}
            </span>
          </div>
        ) : (
          <div
            key={row.key}
            role="row"
            tabIndex={0}
            onClick={() => onOpenTask(row.task.id)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') onOpenTask(row.task.id)
            }}
            style={{ height: ROW_HEIGHT, paddingLeft: GRID_PAD_LEFT }}
            className="group/row flex cursor-pointer items-center gap-1.5 border-b border-border/60 pr-2 hover:bg-accent/40 focus-visible:bg-accent/40 focus-visible:outline-none"
          >
            <div
              className="flex min-w-0 shrink-0 items-center gap-1.5"
              style={{ width: `var(${columnWidthVar(titleColumn.key)})` }}
            >
              {/*  Thụt lề nằm TRONG ô tên, không phải ở lề trái của dòng: đẩy cả
                   dòng sang phải thì mọi cột dữ liệu lệch 18px so với hàng tiêu
                   đề, mà lệch đều nên nhìn vẫn "có vẻ đúng". */}
              <span className="shrink-0" style={{ width: GRID_INDENT }} aria-hidden />

              {isMilestone(row.task) && (
                <Diamond
                  className="size-3 shrink-0 fill-current text-primary"
                  aria-label="Cột mốc"
                />
              )}
              <span
                className={cn(
                  'truncate text-sm',
                  row.task.status === WORK_TASK_STATUS.DONE &&
                    'text-muted-foreground line-through',
                )}
              >
                {row.task.title}
              </span>
            </div>

            {columns.map((col) => (
              <div
                key={col.key}
                className="shrink-0"
                style={{ width: `var(${columnWidthVar(col.key)})` }}
              >
                <TaskListCell
                  column={col}
                  task={row.task}
                  members={members}
                  labelFields={labelFields}
                  canEdit={canEdit}
                  done={row.task.status === WORK_TASK_STATUS.DONE}
                  onSetAssignees={onSetAssignees}
                  onSetDue={onSetDue}
                  onSetStart={onSetStart}
                  onSetStatus={onSetStatus}
                  onSetLabel={onSetLabel}
                />
              </div>
            ))}
          </div>
        ),
      )}
    </div>
  )
}

function HeaderCell({
  column,
  gridRef,
  onResize,
}: {
  column: TaskListColumn
  gridRef: RefObject<HTMLDivElement | null>
  onResize: (key: string, width: number) => void
}) {
  return (
    //  KHÔNG đặt `truncate` ở đây: nó kèm `overflow-hidden`, mà tay cầm kéo giãn
    //  nằm NGOÀI hộp nên bị cắt mất — nhìn như bảng không kéo giãn được.
    <span
      className="relative shrink-0"
      style={{ width: `var(${columnWidthVar(column.key)})` }}
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
