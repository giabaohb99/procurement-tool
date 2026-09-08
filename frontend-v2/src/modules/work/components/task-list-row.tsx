import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { ChevronRight, GripVertical, ListTree, MessageSquare } from 'lucide-react'

import { Checkbox } from '@/shared/ui/checkbox'
import { cn } from '@/shared/utils/cn'
import { columnWidthVar } from '../hooks/use-list-column-widths'
import { taskDraggableId } from '../utils/kanban-drop'
import { COLUMN_GAP, GUIDE_LEFT, LEAD_WIDTH, ROW_PAD_LEFT } from '../utils/list-metrics'
import type { CardFields } from '../types/view-options'
import type { WorkLabelField, WorkMember, WorkTask } from '../types/work'
import { WORK_TASK_STATUS } from '../types/work'
import { TITLE_COLUMN, isFieldVisible, type TaskListColumn } from '../utils/list-columns'
import { PINNED_TITLE_CELL, PINNED_TITLE_FULL_HEIGHT } from '../utils/pinned-title-class'
import { PinnedColumnFade } from './pinned-column-fade'
import { LabelFieldInput } from './label-field-input'
import { TaskAssigneePicker } from './task-assignee-picker'
import { TaskDueCell } from './task-due-cell'
import { TaskStatusSelect } from './task-status-select'
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
  /** Ngày BẮT ĐẦU — cột `start` của bộ «Tùy chỉnh», cũng là mép trái thanh Gantt. */
  onSetStart: (taskId: number, startDate: string) => void
  /**
   * Đặt trạng thái BẤT KỲ (kể cả «Đã hủy») — khác `onToggleDone` chỉ lật hai
   * chiều xong/chưa xong bằng ô tick.
   */
  onSetStatus: (taskId: number, status: number) => void
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
   * Cụm việc con mà dòng này thuộc về — CHỈ dòng việc con mới có.
   *
   * Việc con không nằm trong payload bảng nên `TaskListView` không tra ngược
   * được cha lẫn anh em của nó; cả hai phải đi kèm món đồ đang kéo. Xem
   * `utils/subtask-drop.ts`.
   */
  subtaskGroup?: { parentId: number; siblingIds: number[] }
  /**
   * Cho kéo đổi thứ tự / đổi cột. TẮT khi đang sắp theo tiêu chí khác «Tay»
   * (§3.4) — thả xong mà danh sách tự xếp lại thì người dùng tưởng lỗi.
   */
  draggable?: boolean
  /**
   * Có món nào đang được kéo trong bảng không (bất kể món gì).
   *
   * Khi có thì dòng TẮT hiệu ứng rê chuột: lớp phủ bám sát con trỏ nên dòng nằm
   * dưới nó cứ sáng lên theo, kéo thành một vệt xám chạy dọc bảng lấn át đúng
   * cái khe chờ cần nhìn. Tay cầm kéo cũng hiện luôn — nó đã bị nắm rồi.
   */
  dragActive?: boolean
  /** Con trỏ đang ở chỗ không thả được — chỉ có nghĩa với dòng đang được kéo. */
  dragBlocked?: boolean
  expanded?: boolean
  onToggleExpand?: () => void
  /**
   * Chiều cao CỐ ĐỊNH của dòng (px) — chỉ khung nhìn Gantt truyền, vì mỗi dòng
   * lưới trái bên đó phải cao đúng bằng một hàng của trục thời gian. Bỏ trống
   * thì dòng tự cao theo nội dung như khung nhìn Danh sách xưa nay.
   */
  rowHeight?: number
  /**
   * GHIM ô TÊN vào mép trái khi cuộn ngang — chỉ khung nhìn Gantt bật.
   *
   * Lưới trái bên đó hẹp (mặc định thấy ~3 cột) và tự cuộn ngang để xem nốt các
   * cột còn lại; không ghim thì kéo sang phải là mất luôn tên việc, còn lại một
   * bảng số liệu không biết của ai.
   */
  stickyTitle?: boolean
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
  subtaskGroup,
  draggable = false,
  dragActive = false,
  dragBlocked = false,
  expanded = false,
  onToggleExpand,
  rowHeight,
  stickyTitle = false,
  onOpenTask,
  onToggleDone,
  onRename,
  onSetAssignees,
  onSetDue,
  onSetStart,
  onSetStatus,
  onSetLabel,
}: TaskListRowProps) {
  const { attributes, listeners, setNodeRef, isDragging, isOver, transform, transition } =
    useSortable({
      id: taskDraggableId(task.id),
      disabled: !draggable,
      //  Hai LOẠI món kéo khác nhau đi chung một component: việc con xếp lại
      //  trong cụm của cha, task cha đổi cột. `TaskListView` đọc `type` ở đây để
      //  biết phải giải cú thả theo luật nào.
      data: subtaskGroup
        ? {
            type: 'subtask',
            taskId: task.id,
            parentId: subtaskGroup.parentId,
            siblingIds: subtaskGroup.siblingIds,
            label: task.title,
          }
        : { type: 'task', taskId: task.id, sectionId: task.section_id, label: task.title },
    })

  /*  Cụm việc con là cụm DUY NHẤT chạy hiệu ứng dồn chỗ của dnd-kit
      (`verticalListSortingStrategy` ở `task-list-group.tsx`); dòng việc cha và
      dải tiêu đề nhóm vẫn đứng yên theo lối Lark (`noDisplacement`).

      Không cần rẽ nhánh ở đây: chiến lược nằm ở `SortableContext`, cụm nào dùng
      `noDisplacement` thì `transform` về `null` và `CSS.Translate.toString` trả
      `undefined` — dòng không hề có thuộc tính `transform`. */
  const displaces = Boolean(subtaskGroup)

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
      /*  Dòng VIỆC CHA đứng yên trong lúc kéo (`transform` là `null`, xem
          `list-sorting-strategy.ts`); dòng VIỆC CON thì dạt ra chừa khe theo
          `verticalListSortingStrategy` — chính cái khe ấy là chỗ nó sẽ rơi vào.

          `zIndex` để dòng đang kéo trôi TRÊN các dòng khác: dòng có nền trong
          suốt, chồng lên nhau lúc dạt chỗ thì chữ đè lên chữ.  */
      style={{
        paddingLeft: ROW_PAD_LEFT,
        gap: COLUMN_GAP,
        height: rowHeight,
        transform: CSS.Translate.toString(transform),
        transition,
        zIndex: isDragging ? 1 : undefined,
      }}
      className={cn(
        'group/row relative flex cursor-pointer items-center border-b border-border/60 py-1.5 pr-2',
        'focus-visible:bg-accent/40 focus-visible:outline-none',
        !dragActive && 'hover:bg-accent/40',
        //  Dòng gốc mờ đi — bản đang đi theo con trỏ nằm ở `DragOverlay`.
        //  Dòng việc con còn PHẢI có nền đục: nó trượt qua các dòng anh em nên
        //  nền trong suốt là hai dòng chồng chữ lên nhau ở giữa quãng trượt.
        isDragging && 'opacity-40',
        isDragging && displaces && 'bg-card',
        //  Vệt sáng "thả vào đây": dòng này sẽ bị đẩy xuống, món đang kéo chiếm
        //  chỗ của nó. Không vẽ trên chính dòng đang kéo — nó rê qua chính mình
        //  suốt, sáng lên thì thành nhấp nháy.
        //
        //  Cụm việc con KHÔNG dùng vệt sáng: ở đó các dòng đã dạt ra chừa khe
        //  rồi, tô thêm một dòng nữa là hai tín hiệu nói về hai chỗ khác nhau.
        isOver && !isDragging && !displaces && 'bg-accent',
        //  Ra khỏi cụm anh em = không thả được ở đây (xem `subtask-drop.ts`).
        isDragging && dragBlocked && 'ring-1 ring-destructive',
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
            'text-muted-foreground transition-opacity focus-visible:opacity-100 active:cursor-grabbing',
            //  Đang kéo thì hiện hết tay cầm: chúng theo dòng trôi lên trôi
            //  xuống, để chúng nhấp nháy tắt-bật theo con trỏ thì rối mắt.
            dragActive ? 'opacity-100' : 'opacity-0 group-hover/row:opacity-100',
          )}
        >
          <GripVertical className="size-3.5" />
        </button>
      )}

      {isSubtask && <SubtaskGuide isLast={isLastSubtask} />}

      {/*  Cột TÊN — rộng đúng bằng biến `--wcol-title` mà hàng tiêu đề kéo giãn,
           không còn `flex-1`. `min-w-0` để chữ dài cắt cụt trong lòng nó thay vì
           đẩy các cột số liệu văng khỏi khung. */}
      <div
        className={cn(
          'flex min-w-0 shrink-0 items-center gap-1.5',
          //  Nền ĐỤC và CAO BẰNG CẢ DÒNG là bắt buộc khi ghim: các cột khác
          //  trượt ngang ngay dưới ô này. Nền trong là chữ chồng lên chữ; nền
          //  đục mà thấp hơn dòng thì viên chip cao hơn nó vẫn ló đầu ló đuôi
          //  ra hai bên (xem `PINNED_TITLE_FULL_HEIGHT`).
          stickyTitle && cn(PINNED_TITLE_CELL, PINNED_TITLE_FULL_HEIGHT, 'bg-canvas'),
        )}
        style={{ width: `var(${columnWidthVar(TITLE_COLUMN.key)})` }}
      >
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
            <ChevronRight
              className={cn('size-3.5 transition-transform', expanded && 'rotate-90')}
            />
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

        {/*  Đẩy hai huy hiệu về sát mép phải của ô tên. */}
        <span className="flex-1" aria-hidden />

        {stickyTitle && <PinnedColumnFade />}
      </div>

      {/*  Khoảng đệm ăn hết phần dư của dòng — khớp với khoảng đệm cùng chỗ ở
           hàng tiêu đề, và cũng là vùng bấm để MỞ panel chi tiết (bấm vào chính
           ô tên là sửa tên tại chỗ). */}
      <span className="min-w-0 flex-1" aria-hidden />

      {columns.map((col) => (
        //  Bề rộng đọc từ biến CSS đặt trên khung bao, không phải từ prop: kéo
        //  giãn cột chỉ sửa biến đó nên không dòng nào phải vẽ lại.
        <div
          key={col.key}
          className="shrink-0"
          style={{ width: `var(${columnWidthVar(col.key)})` }}
        >
          <TaskListCell
            column={col}
            task={task}
            members={members}
            labelFields={labelFields}
            canEdit={canEdit}
            done={done}
            onSetAssignees={onSetAssignees}
            onSetDue={onSetDue}
            onSetStart={onSetStart}
            onSetStatus={onSetStatus}
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
      <span
        className={cn('absolute top-0 left-0 w-px bg-border/60', isLast ? 'h-1/2' : 'h-full')}
      />
      <span className="absolute top-0 left-0 h-1/2 w-full rounded-bl-[6px] border-b border-l border-border/60" />
    </span>
  )
}

export interface TaskListCellProps extends Pick<
  TaskRowActions,
  'onSetAssignees' | 'onSetDue' | 'onSetStart' | 'onSetStatus' | 'onSetLabel'
> {
  column: TaskListColumn
  task: WorkTask
  members: WorkMember[]
  labelFields: WorkLabelField[]
  canEdit: boolean
  done: boolean
}

/**
 * MỘT ô dữ liệu của một cột. Xuất ra ngoài vì lưới trái của khung nhìn **Gantt**
 * dùng đúng bộ cột này (`buildListColumns`) — hai bản vẽ ô riêng thì thêm một
 * kiểu trường là phải sửa hai chỗ, và chúng sẽ lệch nhau đúng ở chỗ ít ai mở.
 */
export function TaskListCell({
  column,
  task,
  members,
  canEdit,
  done,
  onSetAssignees,
  onSetDue,
  onSetStart,
  onSetStatus,
  onSetLabel,
}: TaskListCellProps) {
  if (column.key === 'status') {
    return (
      <div onClick={(e) => e.stopPropagation()} role="presentation">
        <TaskStatusSelect
          compact
          status={task.status}
          disabled={!canEdit}
          onChange={(status) => onSetStatus(task.id, status)}
        />
      </div>
    )
  }

  if (column.key === 'start') {
    return (
      <TaskDueCell
        label="Ngày bắt đầu"
        tone={false}
        dueDate={task.start_date}
        done={done}
        canEdit={canEdit}
        onChange={(value) => onSetStart(task.id, value)}
      />
    )
  }

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
        field={field}
        values={task.labels.filter((l) => l.field_id === field.id)}
        members={members}
        disabled={!canEdit}
        onChange={(value) => onSetLabel(task.id, field.id, value)}
      />
    </div>
  )
}
