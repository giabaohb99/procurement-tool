import { useDraggable } from '@dnd-kit/core'
import { memo } from 'react'

import { cn } from '@/shared/utils/cn'
import type { WorkTask } from '../types/work'
import { WORK_TASK_STATUS } from '../types/work'
import { formatDueLabel } from '../utils/due-date'
import type { GanttDragKind } from '../utils/gantt-drag'
import { HANDLE_WIDTH, MIN_LABEL_WIDTH, ROW_HEIGHT } from '../utils/gantt-layout'
import { barGeometry, type GanttTimeline } from '../utils/gantt-scale'
import { chipClass, priorityColor } from '../utils/work-colors'

interface GanttRowProps {
  task: WorkTask
  timeline: GanttTimeline
  canEdit: boolean
  zebra: boolean
  onOpenTask: (taskId: number) => void
}

/**
 * Một hàng của trục thời gian: thanh việc + hai mép kéo.
 *
 * Hàng này **không vẽ lại trong lúc kéo** — kết quả tạm hiện ở lớp phủ
 * (`GanttDragPreview`). Bản đầu cập nhật vị trí thanh theo từng nhịp chuột, kéo
 * theo cả trăm ô lưới ngày vẽ lại cùng lúc nên kéo giật.
 *
 * Việc chưa đặt ngày vẫn có hàng riêng, chỉ là không có thanh — giấu đi thì
 * người dùng đếm thiếu việc mà không biết vì sao (lưới trái vẫn liệt kê nó).
 */
export const GanttRow = memo(function GanttRow({
  task,
  timeline,
  canEdit,
  zebra,
  onOpenTask,
}: GanttRowProps) {
  const bar = barGeometry(task, timeline)
  const nen = cn('relative border-b border-border/60', zebra && 'bg-muted/20')
  if (!bar) return <div style={{ height: ROW_HEIGHT }} className={nen} />

  const xong = task.status === WORK_TASK_STATUS.DONE
  const nhanNgoai = bar.width < MIN_LABEL_WIDTH

  return (
    <div style={{ height: ROW_HEIGHT }} className={nen}>
      <GanttBar
        task={task}
        left={bar.left}
        width={bar.width}
        xong={xong}
        canEdit={canEdit}
        hienNhan={!nhanNgoai}
        onOpenTask={onOpenTask}
      />

      {canEdit && (
        <>
          <GanttHandle task={task} kind="start" left={bar.left} />
          <GanttHandle task={task} kind="end" left={bar.left + bar.width - HANDLE_WIDTH} />
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
          style={{ left: bar.left + bar.width + 6, top: 9, maxWidth: 220 }}
        >
          {task.title}
        </span>
      )}
    </div>
  )
})

interface GanttBarProps {
  task: WorkTask
  left: number
  width: number
  xong: boolean
  canEdit: boolean
  hienNhan: boolean
  onOpenTask: (taskId: number) => void
}

/** Thanh việc — kéo cả thanh để DỜI lịch. */
function GanttBar({ task, left, width, xong, canEdit, hienNhan, onOpenTask }: GanttBarProps) {
  const { setNodeRef, listeners, attributes, isDragging } = useDraggable({
    id: `gantt-move-${task.id}`,
    disabled: !canEdit,
    data: { task, kind: 'move' satisfies GanttDragKind },
  })

  //  Phần tô đậm trong thanh = tiến độ, đúng lối DHTMLX. Việc đã xong là 100%;
  //  còn lại lấy tỉ lệ việc con đã tick (thẻ kanban cũng hiện đúng con số này).
  const tienDo = xong ? 1 : task.subtask_total ? task.subtask_done / task.subtask_total : 0
  const dau = task.start_date || task.due_date
  const cuoi = task.due_date || task.start_date

  return (
    <div
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      onClick={() => onOpenTask(task.id)}
      onKeyDown={(e) => e.key === 'Enter' && onOpenTask(task.id)}
      style={{ left, width, top: 5, height: ROW_HEIGHT - 10 }}
      className={cn(
        'absolute z-10 flex items-center overflow-hidden rounded px-2 text-[11px] font-medium',
        chipClass(priorityColor(task.priority)),
        'ring-1 ring-black/10 ring-inset',
        canEdit ? 'cursor-grab active:cursor-grabbing' : 'cursor-pointer',
        xong && 'opacity-60',
        isDragging && 'opacity-30',
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
 * Mép kéo đổi một đầu ngày. Cố ý là ANH EM của thanh chứ không nằm TRONG thanh:
 * dnd-kit lồng hai vùng kéo vào nhau thì cú bấm vào mép đánh thức luôn thanh
 * cha, và `overflow-hidden` của thanh cũng cắt mất vùng bắt chuột.
 *
 * Không nhận tiêu điểm bàn phím: bàn phím chưa đổi được ngày ở đây (dùng panel
 * chi tiết), thêm hai chặng Tab mỗi hàng chỉ làm rối.
 */
function GanttHandle({ task, kind, left }: { task: WorkTask; kind: GanttDragKind; left: number }) {
  const { setNodeRef, listeners } = useDraggable({
    id: `gantt-${kind}-${task.id}`,
    data: { task, kind },
  })

  return (
    <span
      ref={setNodeRef}
      {...listeners}
      aria-hidden
      style={{ left, width: HANDLE_WIDTH, top: 5, height: ROW_HEIGHT - 10 }}
      className="absolute z-20 cursor-ew-resize rounded-sm hover:bg-foreground/20"
    />
  )
}
