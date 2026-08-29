import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { ChevronRight, GripVertical, ListTree, MessageSquare } from 'lucide-react'

import { Checkbox } from '@/shared/ui/checkbox'
import { cn } from '@/shared/utils/cn'
import { columnWidthVar } from '../hooks/use-list-column-widths'
import { taskDraggableId } from '../utils/kanban-drop'
import { GUIDE_LEFT, LEAD_WIDTH, ROW_PAD_LEFT } from '../utils/list-metrics'
import type { CardFields } from '../types/view-options'
import type { WorkLabelField, WorkMember, WorkTask } from '../types/work'
import { WORK_TASK_STATUS } from '../types/work'
import { isFieldVisible, type TaskListColumn } from '../utils/list-columns'
import { LabelFieldInput } from './label-field-input'
import { TaskAssigneePicker } from './task-assignee-picker'
import { TaskDueCell } from './task-due-cell'
import { TaskTitleCell } from './task-title-cell'

export interface TaskRowActions {
  onOpenTask: (taskId: number) => void
  onToggleDone: (taskId: number, done: boolean) => void
  /**
   * Tick hoàn thành một VIỆC CON — phải biết id việc CHA.
   *
   * Không dùng chung `onToggleDone` được: việc con không nằm trong payload bảng
   * (C-05) nên ảnh lạc quan phải vá vào `subtasks` của khóa `task(parentId)`,
   * còn `onToggleDone` vá vào `board.tasks` rồi làm mới `task(subtaskId)` —
   * chẳng khóa nào là khóa mà dòng này đang đọc, nên ô tick không nhúc nhích.
   */
  onToggleSubtaskDone: (parentId: number, subtaskId: number, done: boolean) => void
  onRename: (taskId: number, title: string) => void
  onSetAssignees: (taskId: number, picIds: number[]) => void
  onSetDue: (taskId: number, dueDate: string) => void
  onSetLabel: (taskId: number, fieldId: number, value: unknown) => void
}

interface TaskListRowProps extends TaskRowActions {
  task: WorkTask
  columns: TaskListColumn[]
  fields: CardFields
  labelFields: WorkLabelField[]
  members: WorkMember[]
  canEdit: boolean
  /** Việc con thụt vào và KHÔNG có mũi tên bung — cây chỉ sâu 2 cấp (C-05). */
  isSubtask?: boolean
  /** Việc con CUỐI cụm: thanh dọc dừng ở khuỷu thay vì chạy tiếp xuống. */
  isLastSubtask?: boolean
  /**
   * Cho kéo đổi thứ tự / đổi cột. TẮT khi đang sắp theo tiêu chí khác «Tay»
   * (§3.4) — thả xong mà danh sách tự xếp lại thì người dùng tưởng lỗi — và
   * luôn tắt với VIỆC CON, vì chúng không nằm trong payload bảng để tính vị trí.
   */
  draggable?: boolean
  expanded?: boolean
  onToggleExpand?: () => void
}

/**
 * MỘT dòng của khung nhìn Danh sách kiểu Lark.
 *
 * Khác `DataTable` dùng chung ở ba điểm cố ý: không kẻ dọc và không sọc chan
 * hòa (Lark chỉ có một vạch ngang mảnh), các ô là ô SỬA ĐƯỢC tại chỗ chứ không
 * phải chữ chết, và ô rỗng vẫn hiện dấu — chứ để trắng trơn thì không ai đoán
 * ra là bấm vào sửa được.
 *
 * Mọi ô nhập đều `stopPropagation`: dòng có `onClick` mở panel chi tiết, không
 * chặn thì mỗi lần đổi người phụ trách lại phải đóng một panel vừa bật lên.
 */
export function TaskListRow({
  task,
  columns,
  fields,
  labelFields,
  members,
  canEdit,
  isSubtask = false,
  isLastSubtask = false,
  draggable = false,
  expanded = false,
  onToggleExpand,
  onOpenTask,
  onToggleDone,
  onRename,
  onSetAssignees,
  onSetDue,
  onSetLabel,
}: TaskListRowProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: taskDraggableId(task.id),
    disabled: !draggable,
    data: { type: 'task', taskId: task.id, sectionId: task.section_id },
  })

  const done = task.status === WORK_TASK_STATUS.DONE
  const hasSubtasks = !isSubtask && task.subtask_total > 0
  const showSubtaskBadge = hasSubtasks && isFieldVisible(fields, 'subtasks')
  const showCommentBadge = task.comment_count > 0 && isFieldVisible(fields, 'comments')

  return (
    <div
      ref={setNodeRef}
      role="row"
      tabIndex={0}
      onClick={() => onOpenTask(task.id)}
      onKeyDown={(e) => {
        if (e.key === 'Enter') onOpenTask(task.id)
      }}
      //  Dòng ĐANG kéo không nhận transform/transition: con trỏ đã có
      //  `DragOverlay` đi theo, cái nằm lại chỉ là chỗ trống mờ. Để nguyên thì
      //  lúc dòng được dời sang cột khác, `transform` vẫn là độ lệch tính từ
      //  cột CŨ nên nó nhảy ngược về chỗ cũ một nhịp rồi mới trườn sang.
      style={{
        paddingLeft: ROW_PAD_LEFT,
        ...(isDragging ? {} : { transform: CSS.Translate.toString(transform), transition }),
      }}
      className={cn(
        'group/row relative flex cursor-pointer items-center gap-2 border-b border-border/60 pr-2 py-1.5',
        'hover:bg-accent/40 focus-visible:bg-accent/40 focus-visible:outline-none',
        //  Dòng gốc mờ đi trong lúc kéo — bản thật đang nằm ở `DragOverlay`.
        isDragging && 'opacity-40',
      )}
    >
      {draggable && (
        <button
          type="button"
          aria-label={`Kéo để xếp lại: ${task.title}`}
          onClick={(e) => e.stopPropagation()}
          {...attributes}
          {...listeners}
          className={cn(
            'absolute top-1/2 left-0.5 -translate-y-1/2 cursor-grab touch-none rounded p-0.5',
            'text-muted-foreground opacity-0 transition-opacity group-hover/row:opacity-100',
            'focus-visible:opacity-100 active:cursor-grabbing',
          )}
        >
          <GripVertical className="size-3.5" />
        </button>
      )}

      {isSubtask && <SubtaskGuide isLast={isLastSubtask} />}

      {/*  Cột TÊN — cột duy nhất co giãn. `min-w-0` để chữ dài cắt cụt trong
           lòng nó thay vì đẩy các cột số liệu văng khỏi khung. */}
      <div className="flex min-w-0 flex-1 items-center gap-1.5">
        {isSubtask && <span className="shrink-0" style={{ width: LEAD_WIDTH }} aria-hidden />}

        {hasSubtasks ? (
          <button
            type="button"
            aria-label={expanded ? 'Thu việc con' : 'Bung việc con'}
            aria-expanded={expanded}
            onClick={(e) => {
              e.stopPropagation()
              onToggleExpand?.()
            }}
            className="rounded p-0.5 text-muted-foreground hover:bg-accent hover:text-foreground"
          >
            <ChevronRight className={cn('size-3.5 transition-transform', expanded && 'rotate-90')} />
          </button>
        ) : (
          !isSubtask && <span className="w-[18px] shrink-0" aria-hidden />
        )}

        <Checkbox
          className="shrink-0 rounded-full"
          checked={done}
          disabled={!canEdit}
          aria-label={`Đánh dấu hoàn thành: ${task.title}`}
          onClick={(e) => e.stopPropagation()}
          onCheckedChange={(checked) => onToggleDone(task.id, checked === true)}
        />

        <TaskTitleCell
          title={task.title}
          done={done}
          canEdit={canEdit}
          onRename={(title) => onRename(task.id, title)}
        />

        {showSubtaskBadge && (
          <span className="flex shrink-0 items-center gap-0.5 text-xs text-muted-foreground">
            <ListTree className="size-3" />
            {task.subtask_done}/{task.subtask_total}
          </span>
        )}
        {showCommentBadge && (
          <span className="flex shrink-0 items-center gap-0.5 text-xs text-muted-foreground">
            <MessageSquare className="size-3" />
            {task.comment_count}
          </span>
        )}

        {/*  Khoảng trống ăn hết phần dư của dòng — đây là vùng bấm để MỞ panel
             chi tiết, tách khỏi ô tên (bấm vào tên là sửa tên tại chỗ). */}
        <span className="flex-1" aria-hidden />
      </div>

      {columns.map((col) => (
        //  Bề rộng đọc từ biến CSS đặt trên khung bao, không phải từ prop: kéo
        //  giãn cột chỉ sửa biến đó nên không dòng nào phải vẽ lại.
        <div key={col.key} className="shrink-0" style={{ width: `var(${columnWidthVar(col.key)})` }}>
          <TaskListCell
            column={col}
            task={task}
            members={members}
            labelFields={labelFields}
            canEdit={canEdit}
            done={done}
            onSetAssignees={onSetAssignees}
            onSetDue={onSetDue}
            onSetLabel={onSetLabel}
          />
        </div>
      ))}
    </div>
  )
}

/**
 * Nhánh nối bo góc dẫn từ việc cha xuống một việc con — đúng kiểu Lark.
 *
 * Thụt lề trơn (chỉ `padding-left`) thì hai cấp trông như hai danh sách rời
 * nhau, nhất là khi việc con cũng có đủ ô như việc cha.
 *
 * Hình được ghép từ HAI mảnh vì cần vừa liền mạch vừa bo góc:
 *
 * - **Khuỷu** — nửa trên của dòng, viền trái + viền dưới cùng một hộp nên góc bo
 *   được bằng `rounded-bl`. Hai vạch rời nhau thì chỗ gặp là một góc vuông sắc.
 * - **Đuôi** — nửa dưới, chỉ có ở việc con KHÔNG phải cuối cụm, nối tiếp xuống
 *   khuỷu của dòng kế. Thiếu nó thì mỗi dòng một khuỷu cụt và cả cụm nhìn rời
 *   rạc; có nó thì thành một thanh dọc chạy suốt, rẽ nhánh vào từng việc con và
 *   dừng hẳn ở cái cuối — nhìn là biết cụm hết ở đâu, khỏi đếm.
 *
 * ⚠️ Phủ TUYỆT ĐỐI theo `inset-y-0` của cả DÒNG, không phải một ô nằm trong
 * luồng. Bản trước để nó `self-stretch` bên trong khối nội dung nên chỉ cao bằng
 * content-box, hụt mất `py-1.5` ở trên và dưới — thành ra giữa hai dòng có một
 * quãng hở 12px và cả cụm vẫn nhìn đứt đoạn dù đã có đuôi nối.
 *
 * `left-[30px]` = `px-2` của dòng (8px) + 22px, tức trùng trục với ô tick của
 * việc CHA. Chỗ giữ chỗ trong luồng là một ô rỗng 46px = đúng phần dẫn đầu của
 * dòng cha (mũi tên bung + ô tick), nên ô tick của việc con thẳng hàng với TÊN
 * việc cha — đúng bậc thang của Lark.
 */
function SubtaskGuide({ isLast }: { isLast: boolean }) {
  return (
    <span
      className="pointer-events-none absolute inset-y-0 w-3"
      style={{ left: GUIDE_LEFT }}
      aria-hidden
    >
      {/*  Nét dọc THẲNG, vẽ trước và độc lập với góc bo.

           Góc bo `rounded-bl` bẻ viền trái ra khỏi trục đúng bằng bán kính, nên
           nếu chỉ trông vào viền của khuỷu thì mỗi mối nối hụt 6px — cụm việc
           con lại nhìn đứt quãng. Nét này chạy thẳng suốt trục và lấp đúng
           quãng ấy; khuỷu bên dưới chỉ còn lo phần cong và nhánh ngang. */}
      <span className={cn('absolute top-0 left-0 w-px bg-border/60', isLast ? 'h-1/2' : 'h-full')} />
      <span className="absolute top-0 left-0 h-1/2 w-full rounded-bl-[6px] border-b border-l border-border/60" />
    </span>
  )
}

interface TaskListCellProps
  extends Pick<TaskRowActions, 'onSetAssignees' | 'onSetDue' | 'onSetLabel'> {
  column: TaskListColumn
  task: WorkTask
  members: WorkMember[]
  labelFields: WorkLabelField[]
  canEdit: boolean
  done: boolean
}

function TaskListCell({
  column,
  task,
  members,
  canEdit,
  done,
  onSetAssignees,
  onSetDue,
  onSetLabel,
}: TaskListCellProps) {
  if (column.key === 'assignees') {
    return (
      <div onClick={(e) => e.stopPropagation()} role="presentation">
        <TaskAssigneePicker
          compact
          assignees={task.assignees}
          members={members}
          disabled={!canEdit}
          onChange={(picIds) => onSetAssignees(task.id, picIds)}
        />
      </div>
    )
  }

  if (column.key === 'due') {
    return (
      <TaskDueCell
        dueDate={task.due_date}
        done={done}
        canEdit={canEdit}
        onChange={(value) => onSetDue(task.id, value)}
      />
    )
  }

  const field = column.field
  if (!field) return null
  return (
    <div onClick={(e) => e.stopPropagation()} role="presentation">
      <LabelFieldInput
        compact
        field={field}
        values={task.labels.filter((l) => l.field_id === field.id)}
        members={members}
        disabled={!canEdit}
        onChange={(value) => onSetLabel(task.id, field.id, value)}
      />
    </div>
  )
}
