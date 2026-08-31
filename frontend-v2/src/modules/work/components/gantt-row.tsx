import { useDraggable } from '@dnd-kit/core'
import { memo } from 'react'

import { cn } from '@/shared/utils/cn'
import type { WorkTask } from '../types/work'
import { WORK_TASK_STATUS } from '../types/work'
import { formatDueLabel } from '../utils/due-date'
import type { GanttDragKind } from '../utils/gantt-drag'
import {
  BAR_PAD,
  HANDLE_WIDTH,
  LINK_DOT,
  MILESTONE_SIZE,
  MIN_LABEL_WIDTH,
  ROW_HEIGHT,
} from '../utils/gantt-layout'
import type { GanttGroupRow } from '../utils/gantt-rows'
import type { LinkSide } from '../utils/gantt-links'
import { barGeometry, isMilestone, milestoneCenter, rangeGeometry, type GanttTimeline } from '../utils/gantt-scale'
import { chipClass } from '../utils/work-colors'

export interface GanttLinkHandlers {
  /** Bắt đầu kéo một mũi tên từ đầu `side` của việc này. */
  onStartLink: (taskId: number, side: LinkSide, event: React.PointerEvent) => void
  /** Việc đang được nhắm làm ĐÍCH của mũi tên đang kéo — tô sáng thanh của nó. */
  linkTargetId: number | null
  /** Có mũi tên nào đang được kéo không: lúc ấy mọi chấm nối đều hiện sẵn. */
  linking: boolean
}

interface GanttTaskRowProps extends GanttLinkHandlers {
  task: WorkTask
  /**
   * Hàng này là VIỆC CON: thanh vẽ mảnh hơn và KHÔNG có chấm nối phụ thuộc —
   * việc con không đặt phụ thuộc được (backend chặn thẳng theo luật C-05), bày
   * chấm ra chỉ mời người dùng ăn một toast 400.
   */
  isSubtask?: boolean
  timeline: GanttTimeline
  /** Màu thanh — tên màu trong `WORK_COLORS`, lấy từ bậc ưu tiên của việc. */
  barColor: string
  canEdit: boolean
  onOpenTask: (taskId: number) => void
}

/**
 * Một hàng VIỆC của trục thời gian: thanh (hoặc hình thoi cột mốc), hai mép kéo
 * đổi ngày, và hai chấm nối phụ thuộc.
 *
 * Hàng này **không vẽ lại trong lúc kéo ngày** — kết quả tạm hiện ở lớp phủ
 * (`GanttDragPreview`). Bản đầu cập nhật vị trí thanh theo từng nhịp chuột, kéo
 * theo cả trăm ô lưới ngày vẽ lại cùng lúc nên kéo giật.
 *
 * Việc chưa đặt ngày vẫn có hàng riêng, chỉ là không có thanh — giấu đi thì
 * người dùng đếm thiếu việc mà không biết vì sao (lưới trái vẫn liệt kê nó).
 */
export const GanttTaskRow = memo(function GanttTaskRow({
  task,
  isSubtask = false,
  timeline,
  barColor,
  canEdit,
  onOpenTask,
  onStartLink,
  linkTargetId,
  linking,
}: GanttTaskRowProps) {
  //  `group/ganttrow` là móc để hai chấm nối chỉ hiện khi rê chuột vào HÀNG này.
  const nen = 'group/ganttrow relative border-b border-border/60'
  //  Thanh việc con mảnh hơn và thụt vào theo chiều DỌC — nhìn là biết ngay nó
  //  thuộc về hàng ngay trên, khỏi phải dò sang lưới trái.
  const barPad = isSubtask ? BAR_PAD + 4 : BAR_PAD
  const barHeight = ROW_HEIGHT - barPad * 2
  const xong = task.status === WORK_TASK_STATUS.DONE
  const laDich = linkTargetId === task.id

  if (isMilestone(task)) {
    const center = milestoneCenter(task, timeline)
    if (center === null) return <div style={{ height: ROW_HEIGHT }} className={nen} />
    return (
      <div style={{ height: ROW_HEIGHT }} className={nen}>
        <GanttMilestone
          task={task}
          center={center}
          xong={xong}
          canEdit={canEdit}
          laDich={laDich}
          linking={linking}
          onOpenTask={onOpenTask}
          onStartLink={onStartLink}
        />
      </div>
    )
  }

  const bar = barGeometry(task, timeline)
  if (!bar) return <div style={{ height: ROW_HEIGHT }} className={nen} />
  const nhanNgoai = bar.width < MIN_LABEL_WIDTH

  return (
    <div style={{ height: ROW_HEIGHT }} className={nen}>
      <GanttBar
        task={task}
        barColor={barColor}
        left={bar.left}
        width={bar.width}
        top={barPad}
        height={barHeight}
        xong={xong}
        canEdit={canEdit}
        laDich={laDich}
        hienNhan={!nhanNgoai}
        onOpenTask={onOpenTask}
      />

      {canEdit && (
        <>
          <GanttHandle task={task} kind="start" left={bar.left} top={barPad} height={barHeight} />
          <GanttHandle
            task={task}
            kind="end"
            left={bar.left + bar.width - HANDLE_WIDTH}
            top={barPad}
            height={barHeight}
          />
          {!isSubtask && (
            <>
              <LinkDot
                taskId={task.id}
                side="start"
                left={bar.left - LINK_DOT - 2}
                visible={linking}
                onStartLink={onStartLink}
              />
              <LinkDot
                taskId={task.id}
                side="end"
                left={bar.left + bar.width + 2}
                visible={linking}
                onStartLink={onStartLink}
              />
            </>
          )}
        </>
      )}

      {/*  Tên đặt ngoài thanh khi thanh quá ngắn. Không bắt sự kiện chuột để nó
          không che mất mép kéo của thanh bên cạnh. */}
      {nhanNgoai && (
        <span
          className={cn(
            'pointer-events-none absolute z-10 truncate text-[11px] whitespace-nowrap',
            xong ? 'text-muted-foreground line-through' : 'text-foreground/80',
          )}
          style={{ left: bar.left + bar.width + LINK_DOT + 8, top: 10, maxWidth: 220 }}
        >
          {task.title}
        </span>
      )}
    </div>
  )
})

/**
 * Hàng NHÓM: thanh tổng trải từ ngày sớm nhất tới hạn muộn nhất của các việc
 * trong nhóm, dáng dẹt và có hai chân quặp xuống đúng kiểu thanh tóm tắt của
 * Gantt cổ điển — nhìn là phân biệt ngay với thanh việc.
 *
 * Không kéo được: ngày của nó là ngày TÍNH RA từ các việc con, kéo thì không
 * biết phải dời việc nào.
 */
export function GanttGroupBar({
  row,
  timeline,
}: {
  row: GanttGroupRow
  timeline: GanttTimeline
}) {
  const bar = row.range ? rangeGeometry(row.range.start, row.range.due, timeline) : null
  return (
    <div style={{ height: ROW_HEIGHT }} className="relative border-b bg-muted/30">
      {bar && (
        <div
          className="absolute rounded-[3px] bg-foreground/70"
          style={{ left: bar.left, width: bar.width, top: ROW_HEIGHT / 2 - 5, height: 10 }}
          title={`${row.group.name} · ${formatDueLabel(row.range?.start ?? '')} → ${formatDueLabel(row.range?.due ?? '')}`}
        >
          {/* Phần tô đậm = tỉ lệ việc đã hoàn thành trong nhóm. */}
          {row.progress > 0 && (
            <span
              aria-hidden
              className="absolute inset-y-0 left-0 rounded-l-[3px] bg-emerald-400/80"
              style={{ width: `${Math.min(100, row.progress * 100)}%` }}
            />
          )}
          <span
            aria-hidden
            className="absolute top-full -left-px border-t-[6px] border-l-[6px] border-t-foreground/70 border-l-transparent"
          />
          <span
            aria-hidden
            className="absolute top-full -right-px border-t-[6px] border-r-[6px] border-t-foreground/70 border-r-transparent"
          />
        </div>
      )}
    </div>
  )
}

interface GanttBarProps {
  task: WorkTask
  barColor: string
  left: number
  width: number
  top: number
  height: number
  xong: boolean
  canEdit: boolean
  laDich: boolean
  hienNhan: boolean
  onOpenTask: (taskId: number) => void
}

/** Thanh việc — kéo cả thanh để DỜI lịch. */
function GanttBar({
  task,
  barColor,
  left,
  width,
  top,
  height,
  xong,
  canEdit,
  laDich,
  hienNhan,
  onOpenTask,
}: GanttBarProps) {
  const { setNodeRef, listeners, attributes, isDragging } = useDraggable({
    id: `gantt-move-${task.id}`,
    disabled: !canEdit,
    data: { task, kind: 'move' satisfies GanttDragKind },
  })

  //  Phần tô đậm trong thanh = tiến độ. Việc đã xong là 100%; còn lại lấy tỉ lệ
  //  việc con đã tick (thẻ kanban cũng hiện đúng con số này).
  const tienDo = xong ? 1 : task.subtask_total ? task.subtask_done / task.subtask_total : 0
  const dau = task.start_date || task.due_date
  const cuoi = task.due_date || task.start_date

  return (
    <div
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      data-gantt-bar
      data-task-id={task.id}
      onClick={() => onOpenTask(task.id)}
      onKeyDown={(e) => e.key === 'Enter' && onOpenTask(task.id)}
      style={{ left, width, top, height }}
      className={cn(
        'absolute z-10 flex items-center overflow-hidden rounded px-2 text-[11px] font-medium',
        chipClass(barColor),
        'ring-1 ring-black/10 ring-inset',
        canEdit ? 'cursor-grab active:cursor-grabbing' : 'cursor-pointer',
        xong && 'opacity-60',
        isDragging && 'opacity-30',
        laDich && 'ring-2 ring-primary',
      )}
      title={`${task.title} · ${formatDueLabel(dau)} → ${formatDueLabel(cuoi)}`}
    >
      {/* Dải tiến độ nằm DƯỚI chữ, không che tiêu đề. */}
      {tienDo > 0 && (
        <span
          aria-hidden
          className="absolute inset-y-0 left-0 bg-current/20"
          style={{ width: `${Math.min(100, tienDo * 100)}%` }}
        />
      )}
      {hienNhan && <span className="relative truncate">{task.title}</span>}
    </div>
  )
}

/**
 * CỘT MỐC (B-14) — hình thoi tại đúng ngày, không phải một thanh.
 *
 * Kéo được như thanh (dời mốc sang ngày khác) nên vẫn là một `useDraggable` với
 * `kind: 'move'`; `datesToSave` chỉ ghi `due_date` vì mốc không có ngày bắt đầu.
 */
function GanttMilestone({
  task,
  center,
  xong,
  canEdit,
  laDich,
  linking,
  onOpenTask,
  onStartLink,
}: {
  task: WorkTask
  center: number
  xong: boolean
  canEdit: boolean
  laDich: boolean
  linking: boolean
  onOpenTask: (taskId: number) => void
  onStartLink: GanttLinkHandlers['onStartLink']
}) {
  const { setNodeRef, listeners, attributes, isDragging } = useDraggable({
    id: `gantt-move-${task.id}`,
    disabled: !canEdit,
    data: { task, kind: 'move' satisfies GanttDragKind },
  })

  return (
    <>
      <div
        ref={setNodeRef}
        {...attributes}
        {...listeners}
        data-gantt-bar
        data-task-id={task.id}
        onClick={() => onOpenTask(task.id)}
        onKeyDown={(e) => e.key === 'Enter' && onOpenTask(task.id)}
        style={{
          left: center - MILESTONE_SIZE / 2,
          top: ROW_HEIGHT / 2 - MILESTONE_SIZE / 2,
          width: MILESTONE_SIZE,
          height: MILESTONE_SIZE,
        }}
        className={cn(
          'absolute z-10 rotate-45 rounded-[2px] bg-primary ring-1 ring-black/10',
          canEdit ? 'cursor-grab active:cursor-grabbing' : 'cursor-pointer',
          xong && 'opacity-60',
          isDragging && 'opacity-30',
          laDich && 'ring-2 ring-primary',
        )}
        title={`${task.title} · Cột mốc ${formatDueLabel(task.due_date || task.start_date)}`}
      />
      <span
        className={cn(
          'pointer-events-none absolute z-10 truncate text-[11px] font-medium whitespace-nowrap',
          xong ? 'text-muted-foreground line-through' : 'text-foreground/80',
        )}
        style={{ left: center + MILESTONE_SIZE, top: 10, maxWidth: 220 }}
      >
        {task.title}
      </span>
      {canEdit && (
        <LinkDot
          taskId={task.id}
          side="end"
          left={center + MILESTONE_SIZE / 2 + 2}
          visible={linking}
          onStartLink={onStartLink}
        />
      )}
    </>
  )
}

/**
 * Mép kéo đổi một đầu ngày. Cố ý là ANH EM của thanh chứ không nằm TRONG thanh:
 * dnd-kit lồng hai vùng kéo vào nhau thì cú bấm vào mép đánh thức luôn thanh
 * cha, và `overflow-hidden` của thanh cũng cắt mất vùng bắt chuột.
 *
 * Không nhận tiêu điểm bàn phím: bàn phím chưa đổi được ngày ở đây (dùng panel
 * chi tiết), thêm hai chặng Tab mỗi hàng chỉ làm rối.
 */
function GanttHandle({
  task,
  kind,
  left,
  top,
  height,
}: {
  task: WorkTask
  kind: GanttDragKind
  left: number
  top: number
  height: number
}) {
  const { setNodeRef, listeners } = useDraggable({
    id: `gantt-${kind}-${task.id}`,
    data: { task, kind },
  })

  return (
    <span
      ref={setNodeRef}
      {...listeners}
      aria-hidden
      //  Mang theo id việc để phép dò đích của cú kéo NỐI PHỤ THUỘC nhận ra nó
      //  thuộc về ai — mép này đè lên thanh, thiếu nó thì thả vào những việc chỉ
      //  rộng một ngày luôn trượt (xem `use-gantt-link-draft.hitTest`).
      data-task-id={task.id}
      style={{ left, width: HANDLE_WIDTH, top, height }}
      className="absolute z-20 cursor-ew-resize rounded-sm hover:bg-foreground/20"
    />
  )
}

/**
 * Chấm NỐI PHỤ THUỘC ở một đầu thanh — kéo từ đây sang một việc khác là tạo mũi
 * tên (B-15).
 *
 * Nằm HẲN NGOÀI thanh: đặt lồng bên trong thì nó ăn mất chỗ của mép kéo đổi
 * ngày, và ở mức phóng Tháng (thanh rộng vài pixel) thì chồng lên nhau hết.
 *
 * Ẩn cho tới khi rê chuột vào hàng — hiện sẵn thì mỗi hàng có thêm hai chấm,
 * biểu đồ trăm việc thành một bãi chấm. Đang kéo một mũi tên thì hiện HẾT, vì
 * lúc ấy chúng chính là các đích để ngắm.
 *
 * Dùng `pointerdown` thô chứ không qua dnd-kit: dnd-kit trong khung này đang lo
 * việc kéo NGÀY, cho hai loại kéo khác nghĩa đi chung một `DndContext` thì
 * `onDragEnd` phải đoán xem cú thả vừa rồi là loại nào — đúng chỗ dễ nhầm nhất.
 */
function LinkDot({
  taskId,
  side,
  left,
  visible,
  onStartLink,
}: {
  taskId: number
  side: LinkSide
  left: number
  visible: boolean
  onStartLink: GanttLinkHandlers['onStartLink']
}) {
  return (
    <span
      role="presentation"
      aria-hidden
      data-task-id={taskId}
      title={side === 'end' ? 'Kéo để nối việc sau' : 'Kéo để nối việc trước'}
      onPointerDown={(e) => {
        e.stopPropagation()
        e.preventDefault()
        onStartLink(taskId, side, e)
      }}
      onClick={(e) => e.stopPropagation()}
      style={{
        left,
        top: ROW_HEIGHT / 2 - LINK_DOT / 2,
        width: LINK_DOT,
        height: LINK_DOT,
      }}
      className={cn(
        'absolute z-30 cursor-crosshair rounded-full border-2 border-primary bg-background transition-opacity',
        visible ? 'opacity-100' : 'opacity-0 group-hover/ganttrow:opacity-100',
      )}
    />
  )
}
