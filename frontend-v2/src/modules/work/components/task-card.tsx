import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import {
  CalendarDays,
  CircleDot,
  GitBranch,
  ListChecks,
  MessageSquare,
  Tag as TagIcon,
  type LucideIcon,
} from 'lucide-react'
import { memo, type ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'
import { labelFieldId, type CardFields, type CardFieldKey } from '../types/view-options'
import type { WorkLabelField, WorkTag, WorkTask } from '../types/work'
import { WORK_ASSIGNEE_KIND, WORK_PRIORITY, WORK_TASK_STATUS } from '../types/work'
import { dueTone, dueToneClass, formatDueLabel } from '../utils/due-date'
import { taskDraggableId } from '../utils/kanban-drop'
import { chipClass, priorityColor } from '../utils/work-colors'

interface TaskCardBodyProps {
  task: WorkTask
  tags: WorkTag[]
  labelFields: WorkLabelField[]
  fields: CardFields
  className?: string
}

interface TaskCardProps extends TaskCardBodyProps {
  onOpen: (taskId: number) => void
  /** Khóa kéo thả khi đang sắp xếp khác «Tay» (§3.4). */
  dragDisabled?: boolean
  /**
   * Giấu hẳn thẻ mờ nằm lại, nhưng VẪN CHỪA KHE. Bật khi thẻ đã được dời sang
   * cột khác — xem `kanban-board.tsx`.
   */
  hideGhost?: boolean
}

/**
 * Thẻ việc trên kanban — vỏ KÉO THẢ, còn phần nhìn thấy nằm ở `TaskCardBody`.
 *
 * Tách hai lớp vì lớp phủ (`DragOverlay`) phải vẽ lại đúng cái thẻ này mà KHÔNG
 * được gọi `useSortable` lần nữa: hai nút cùng một `id` trong một `DndContext`
 * thì dnd-kit đo nhầm ô đích.
 */
export function TaskCard({
  task,
  tags,
  labelFields,
  fields,
  onOpen,
  dragDisabled,
  hideGhost,
}: TaskCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: taskDraggableId(task.id),
    disabled: dragDisabled,
    data: { type: 'task', taskId: task.id, sectionId: task.section_id },
  })

  return (
    <div
      ref={setNodeRef}
      //  `transition` ở đây là của dnd-kit (hiệu ứng dồn chỗ khi thẻ khác chen
      //  vào). TUYỆT ĐỐI không gắn thêm lớp `transition` của Tailwind lên nút
      //  này: lớp đó phủ cả `transform`, nên thẻ đang kéo bị nội suy 150ms và
      //  lết theo sau con trỏ — đúng cái cảm giác "kéo bị lag".
      //
      //  CHÍNH THẺ ĐANG KÉO thì KHÔNG nhận transform/transition. Con trỏ đã có
      //  `DragOverlay` đi theo rồi; cái nằm lại đây chỉ là chỗ trống mờ. Để
      //  nguyên hai giá trị của dnd-kit thì lúc thẻ được dời sang cột khác,
      //  `transform` vẫn còn là độ lệch tính từ cột CŨ và `transition` nội suy
      //  200ms — thẻ nhảy ngược về cột cũ một nhịp rồi mới trườn sang cột mới.
      style={
        isDragging ? undefined : { transform: CSS.Translate.toString(transform), transition }
      }
      {...attributes}
      {...listeners}
      onClick={() => onOpen(task.id)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter') onOpen(task.id)
      }}
      //  `invisible` = `visibility: hidden`, KHÔNG phải `hidden`: thẻ tàng hình
      //  nhưng vẫn chiếm chỗ, nên cột đích vẫn mở khe ra đúng như khi kéo trong
      //  một cột. Bỏ vẽ hẳn thì cột đích không nhúc nhích, chẳng biết rơi vào đâu.
      className={cn('cursor-pointer', isDragging && (hideGhost ? 'invisible' : 'opacity-40'))}
    >
      <TaskCardBody task={task} tags={tags} labelFields={labelFields} fields={fields} />
    </div>
  )
}

/**
 * Phần nhìn thấy của thẻ — giải phẫu theo §4 của `05-giao-dien.md`.
 *
 * Tiêu đề luôn hiện, cắt hai dòng. Mọi thứ còn lại tắt được, và tắt thì KHÔNG
 * vẽ hàng rỗng: thẻ ba hàng trắng nhìn như đang tải dở.
 *
 * `memo` vì mỗi lần thẻ đang kéo đi qua một ô mới, dnd-kit vẽ lại cả cột để dồn
 * chỗ; không chặn thì hàng chục thẻ dựng lại chip/avatar theo từng nhịp chuột.
 */
export const TaskCardBody = memo(function TaskCardBody({
  task,
  tags,
  labelFields,
  fields,
  className,
}: TaskCardBodyProps) {
  const done = task.status === WORK_TASK_STATUS.DONE
  const rows = fields
    .filter((f) => f.visible)
    .map((f) => buildFieldRow(f.key, task, tags, labelFields))
    //  Trường bật nhưng thẻ này CHƯA CÓ giá trị thì bỏ hẳn dòng, không vẽ
    //  "Hạn chót —". Thẻ mười dòng gạch ngang thì đọc còn mệt hơn không có gì.
    .filter((row): row is FieldRow => row !== null)

  return (
    <div
      className={cn(
        'rounded-lg border bg-card p-3 text-left shadow-sm transition-colors hover:border-primary/40',
        done && 'opacity-70',
        className,
      )}
    >
      <p className={cn('line-clamp-2 text-sm font-medium', done && 'line-through')}>
        {task.title}
      </p>

      {rows.length > 0 && (
        <div className="mt-2 space-y-1.5">
          {rows.map((row) => (
            <div key={row.key} className="flex items-center gap-2 text-xs">
              {/*  Nhãn trường có bề rộng CỐ ĐỊNH để mọi giá trị thẳng hàng dọc —
                  co theo chữ thì mỗi dòng lệch một kiểu, nhìn như bảng gãy. */}
              <span className="flex w-[104px] shrink-0 items-center gap-1.5 text-muted-foreground">
                <row.icon className="size-3.5 shrink-0" />
                <span className="truncate">{row.label}</span>
              </span>
              <span className="flex min-w-0 flex-wrap items-center gap-1">{row.value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
})

interface FieldRow {
  key: string
  icon: LucideIcon
  label: string
  value: ReactNode
}

/**
 * Một dòng trường trên thẻ: `biểu tượng · tên trường · giá trị`, theo đúng cách
 * Lark vẽ thẻ. `null` = thẻ này không có gì để khoe ở trường đó.
 */
function buildFieldRow(
  key: CardFieldKey,
  task: WorkTask,
  tags: WorkTag[],
  labelFields: WorkLabelField[],
): FieldRow | null {
  const fieldId = labelFieldId(key)
  if (fieldId !== null) {
    const field = labelFields.find((f) => f.id === fieldId)
    const chosen = task.labels.find((l) => l.field_id === fieldId)
    const option = field?.options.find((o) => o.id === chosen?.option_id)
    if (!field || !option) return null
    return {
      key,
      icon: CircleDot,
      label: field.name,
      value: <Chip color={option.color}>{option.name}</Chip>,
    }
  }

  switch (key) {
    case 'priority': {
      if (task.priority === WORK_PRIORITY.NONE) return null
      return {
        key,
        icon: CircleDot,
        label: 'Độ ưu tiên',
        value: <Chip color={priorityColor(task.priority)}>{`P${task.priority}`}</Chip>,
      }
    }
    case 'tags': {
      const chosen = tags.filter((t) => task.tag_ids.includes(t.id))
      if (chosen.length === 0) return null
      return {
        key,
        icon: TagIcon,
        label: 'Tag',
        value: chosen.map((t) => (
          <Chip key={t.id} color={t.color}>
            {t.name}
          </Chip>
        )),
      }
    }
    case 'assignees': {
      const people = task.assignees.filter((a) => a.kind === WORK_ASSIGNEE_KIND.PIC)
      if (people.length === 0) return null
      return {
        key,
        icon: ListChecks,
        label: 'Phụ trách',
        value: (
          <span className="flex items-center -space-x-1.5">
            {/* Tối đa 3 avatar rồi "+n" — đông người mà xếp hết thì thẻ dài ra
                gấp đôi và cột kanban tụt hết xuống dưới màn hình. */}
            {people.slice(0, 3).map((a) => (
              <span
                key={a.employee_id}
                title={a.employee_name || `Nhân sự #${a.employee_id}`}
                className="grid size-5 place-items-center rounded-full border bg-accent text-[10px] font-medium text-accent-foreground"
              >
                {initials(a.employee_name)}
              </span>
            ))}
            {people.length > 3 && (
              <span className="pl-2.5 text-muted-foreground">+{people.length - 3}</span>
            )}
          </span>
        ),
      }
    }
    case 'due': {
      if (!task.due_date) return null
      const done = task.status === WORK_TASK_STATUS.DONE
      return {
        key,
        icon: CalendarDays,
        label: 'Hạn chót',
        value: (
          <span className={dueToneClass(dueTone(task.due_date, done))}>
            {formatDueLabel(task.due_date)}
          </span>
        ),
      }
    }
    case 'subtasks': {
      if (task.subtask_total === 0) return null
      return {
        key,
        icon: GitBranch,
        label: 'Việc con',
        value: `${task.subtask_done}/${task.subtask_total}`,
      }
    }
    case 'comments': {
      if (task.comment_count === 0) return null
      return { key, icon: MessageSquare, label: 'Bình luận', value: task.comment_count }
    }
    default:
      return null
  }
}

function Chip({ color, children }: { color: string; children: React.ReactNode }) {
  return (
    <span className={cn('rounded px-1.5 py-0.5 text-[11px] font-medium', chipClass(color))}>
      {children}
    </span>
  )
}

/** Chữ tắt trên avatar: hai chữ cái đầu của TỪ CUỐI — tên Việt gọi theo tên. */
function initials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean)
  if (words.length === 0) return '?'
  return words[words.length - 1].slice(0, 2).toUpperCase()
}
