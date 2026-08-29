import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { ChevronRight, Plus } from 'lucide-react'
import { useMemo, useState } from 'react'

import { cn } from '@/shared/utils/cn'
import { useWorkTask } from '../hooks/use-work-board'
import type { CardFields } from '../types/view-options'
import type { WorkLabelField, WorkMember, WorkTask } from '../types/work'
import type { TaskGroup } from '../utils/group-tasks'
import { columnDroppableId, taskDraggableId } from '../utils/kanban-drop'
import type { TaskListColumn } from '../utils/list-columns'
import { ROW_PAD_LEFT } from '../utils/list-metrics'
import { dotClass } from '../utils/work-colors'
import { TaskDraftRow, type NewTaskDraft } from './task-draft-row'
import { TaskListRow, type TaskRowActions } from './task-list-row'

interface TaskListGroupProps extends TaskRowActions {
  group: TaskGroup
  columns: TaskListColumn[]
  fields: CardFields
  labelFields: WorkLabelField[]
  members: WorkMember[]
  canEdit: boolean
  collapsed: boolean
  onToggleCollapse: () => void
  /** Nhân sự đang đăng nhập — dòng nháp gán sẵn làm người phụ trách. */
  defaultPicId?: number
  /** Cho kéo xếp lại — tắt khi đang sắp theo tiêu chí khác «Tay» (§3.4). */
  draggable: boolean
  /** Thêm việc vào ĐÚNG cột này — `sectionId` null với nhóm "Chưa phân cột". */
  onAddTask: (sectionId: number | null, draft: NewTaskDraft) => void
}

/**
 * Một NHÓM trên khung nhìn Danh sách: tiêu đề thu/mở + các dòng + «Việc mới».
 *
 * Số đếm trên tiêu đề là số việc SAU KHI LỌC, không phải tổng của cột — người
 * dùng đang nhìn bộ lọc nào thì con số phải nói về đúng bộ lọc ấy, chứ hiện
 * tổng thì nó mâu thuẫn ngay với số dòng đếm được bên dưới.
 */
export function TaskListGroup({
  group,
  columns,
  fields,
  labelFields,
  members,
  canEdit,
  collapsed,
  onToggleCollapse,
  defaultPicId,
  draggable,
  onAddTask,
  ...rowActions
}: TaskListGroupProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null)

  /*  Vùng hứng của CẢ nhóm, kể cả khi nhóm rỗng: không có nó thì cột chưa có
      việc nào không nhận được cú thả, mà đó lại đúng là lúc người ta hay kéo
      việc sang. `sectionId` null (nhóm "Chưa phân cột") không phải cột thật nên
      không đăng ký vùng thả — máy chủ cần một `section_id` có thật.  */
  const { setNodeRef, isOver } = useDroppable({
    id: group.sectionId === null ? `ungrouped-${group.key}` : columnDroppableId(group.sectionId),
    disabled: !draggable || group.sectionId === null,
  })

  const sortableIds = useMemo(
    () => group.tasks.map((t) => taskDraggableId(t.id)),
    [group.tasks],
  )

  return (
    <section ref={setNodeRef} className={cn(isOver && 'bg-accent/20')}>
      <button
        type="button"
        onClick={onToggleCollapse}
        aria-expanded={!collapsed}
        className="flex w-full items-center gap-1.5 px-2 py-2 text-left hover:bg-accent/30"
      >
        <ChevronRight
          className={cn(
            'size-4 text-muted-foreground transition-transform',
            !collapsed && 'rotate-90',
          )}
        />
        <span className={cn('size-2 shrink-0 rounded-full', dotClass(group.color))} />
        <span className="text-sm font-medium">{group.name}</span>
        <span className="text-xs tabular-nums text-muted-foreground">{group.tasks.length}</span>
      </button>

      {!collapsed && (
        <>
          <SortableContext items={sortableIds} strategy={verticalListSortingStrategy}>
            {group.tasks.map((task) => (
              <TaskRowWithSubtasks
                key={task.id}
                task={task}
                columns={columns}
                fields={fields}
                labelFields={labelFields}
                members={members}
                canEdit={canEdit}
                draggable={draggable && canEdit}
                expanded={expandedId === task.id}
                onToggleExpand={() => setExpandedId((prev) => (prev === task.id ? null : task.id))}
                {...rowActions}
              />
            ))}
          </SortableContext>

          {canEdit && (
            <NewTaskRow
              columns={columns}
              members={members}
              defaultPicId={defaultPicId}
              onAdd={(draft) => onAddTask(group.sectionId, draft)}
            />
          )}
        </>
      )}
    </section>
  )
}

interface TaskRowWithSubtasksProps extends TaskRowActions {
  task: WorkTask
  columns: TaskListColumn[]
  fields: CardFields
  labelFields: WorkLabelField[]
  members: WorkMember[]
  canEdit: boolean
  draggable: boolean
  expanded: boolean
  onToggleExpand: () => void
}

/**
 * Một dòng cha kèm các dòng việc con khi được bung.
 *
 * Việc con nạp LƯỜI qua `GET /tasks/{id}` chứ không nằm sẵn trong payload bảng:
 * bảng đang trả 41 việc thì kèm luôn 82 việc con là gấp ba lượng dữ liệu cho
 * một thứ đa số người dùng không bung. Dùng lại đúng query của panel chi tiết
 * nên bung ở đây rồi mở panel là đã có sẵn trong cache, không gọi thêm lượt nào.
 */
function TaskRowWithSubtasks({ task, expanded, ...rest }: TaskRowWithSubtasksProps) {
  const { data: detail } = useWorkTask(expanded ? task.id : undefined)

  return (
    <>
      <TaskListRow task={task} expanded={expanded} {...rest} />
      {expanded &&
        (detail?.subtasks ?? []).map((sub, index, all) => (
          <TaskListRow
            key={sub.id}
            task={sub}
            isSubtask
            isLastSubtask={index === all.length - 1}
            {...rest}
            //  Đè SAU `{...rest}`: việc con đi đường tick riêng, gắn sẵn id cha.
            onToggleDone={(subtaskId, done) => rest.onToggleSubtaskDone(task.id, subtaskId, done)}
          />
        ))}
    </>
  )
}

function NewTaskRow({
  columns,
  members,
  defaultPicId,
  onAdd,
}: {
  columns: TaskListColumn[]
  members: WorkMember[]
  defaultPicId?: number
  onAdd: (draft: NewTaskDraft) => void
}) {
  const [typing, setTyping] = useState(false)

  if (typing) {
    return (
      <TaskDraftRow
        columns={columns}
        members={members}
        defaultPicId={defaultPicId}
        onCancel={() => setTyping(false)}
        onSave={onAdd}
      />
    )
  }

  /*  Cùng bố cục dẫn đầu với `TaskListRow`: chỗ trống bằng đúng nút bung việc
      con, rồi dấu «+» đứng đúng chỗ ô tick. Nhờ vậy chữ «Việc mới» thẳng hàng
      với tên việc ngay bên trên, thay vì thụt một khoảng lệch nhìn thấy rõ.  */
  return (
    <button
      type="button"
      onClick={() => setTyping(true)}
      style={{ paddingLeft: ROW_PAD_LEFT }}
      className="flex w-full items-center gap-1.5 border-b border-border/60 bg-muted/30 py-1.5 pr-2 text-left text-sm text-muted-foreground hover:bg-accent/40 hover:text-foreground"
    >
      <span className="w-[18px] shrink-0" aria-hidden />
      <Plus className="size-4 shrink-0" />
      <span className="px-1">Việc mới</span>
    </button>
  )
}
