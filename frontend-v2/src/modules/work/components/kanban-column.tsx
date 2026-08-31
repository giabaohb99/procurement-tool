import { useDroppable } from '@dnd-kit/core'
import { SortableContext, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { MoreHorizontal, Plus } from 'lucide-react'
import { useMemo, useState } from 'react'

import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { Input } from '@/shared/ui/input'
import { cn } from '@/shared/utils/cn'
import type { WorkLabelField, WorkSection, WorkTask } from '../types/work'
import { dotClass } from '../utils/work-colors'
import { columnDroppableId, columnSortableId, taskDraggableId } from '../utils/kanban-drop'
import type { CardFields } from '../types/view-options'
import { TaskCard } from './task-card'

interface KanbanColumnProps {
  section: WorkSection
  tasks: WorkTask[]
  labelFields: WorkLabelField[]
  fields: CardFields
  canEdit: boolean
  canManage: boolean
  dragDisabled?: boolean
  /** Thẻ phải tàng hình vì đã được kéo sang cột khác; `null` = không có. */
  hideGhostTaskId?: number | null
  onOpenTask: (taskId: number) => void
  /** Tick xong việc ngay trên thẻ, khỏi phải mở panel chi tiết. */
  onToggleDone: (taskId: number, done: boolean) => void
  onCreateTask: (sectionId: number, title: string) => void
  onRenameSection: (section: WorkSection) => void
  onDeleteSection: (section: WorkSection) => void
}

/**
 * Một cột kanban: tiêu đề + chấm màu + SỐ ĐẾM + menu cột + ô thêm nhanh cuối cột.
 *
 * Cột là vùng THẢ riêng (`useDroppable`) chứ không chỉ là danh sách sắp xếp —
 * không thế thì kéo thẻ vào cột đang RỖNG sẽ không có gì bắt được cú thả.
 */
export function KanbanColumn({
  section,
  tasks,
  labelFields,
  fields,
  canEdit,
  canManage,
  dragDisabled,
  hideGhostTaskId = null,
  onOpenTask,
  onToggleDone,
  onCreateTask,
  onRenameSection,
  onDeleteSection,
}: KanbanColumnProps) {
  const [adding, setAdding] = useState(false)
  const [title, setTitle] = useState('')
  const { setNodeRef } = useDroppable({
    id: columnDroppableId(section.id),
    data: { type: 'section', sectionId: section.id },
  })

  //  Cả cột là một món kéo được để đổi thứ tự cột. `listeners` chỉ gắn lên phần
  //  TIÊU ĐỀ — gắn lên cả cột thì mỗi lần kéo một thẻ bên trong là kéo luôn cả
  //  cột. Chỉ ADMIN trở lên mới xếp được cột (cột là cấu hình của dự án).
  const {
    attributes,
    listeners,
    setNodeRef: setColumnRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: columnSortableId(section.id),
    disabled: !canManage,
    data: { type: 'column', sectionId: section.id },
  })

  //  Danh sách id phải GIỮ NGUYÊN tham chiếu giữa các lần vẽ, không thì mỗi nhịp
  //  kéo là `SortableContext` tưởng cột vừa đổi và đo lại toàn bộ thẻ.
  const items = useMemo(() => tasks.map((t) => taskDraggableId(t.id)), [tasks])

  function saveNewTask() {
    const value = title.trim()
    if (!value) {
      setAdding(false)
      return
    }
    onCreateTask(section.id, value)
    setTitle('')   // giữ ô mở để gõ tiếp việc kế, như Lark
  }

  return (
    <div
      ref={setColumnRef}
      style={{ transform: CSS.Translate.toString(transform), transition }}
      className={cn(
        'flex w-72 shrink-0 flex-col rounded-lg bg-muted/40',
        isDragging && 'opacity-50',
      )}
    >
      {/*  Tiêu đề là TAY CẦM kéo cột. Nút menu bên phải nằm ngoài tay cầm nên
          vẫn bấm được bình thường. */}
      <div
        {...attributes}
        {...listeners}
        className={cn('flex items-center gap-2 px-3 py-2', canManage && 'cursor-grab')}
      >
        <span className={cn('size-2 rounded-full', dotClass(section.color))} />
        <span className="flex-1 truncate text-sm font-semibold">{section.name}</span>
        <span className="text-xs text-muted-foreground">{tasks.length}</span>
        {canManage && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="size-6">
                <MoreHorizontal className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onRenameSection(section)}>
                Đổi tên / màu
              </DropdownMenuItem>
              <DropdownMenuItem
                variant="destructive"
                onClick={() => onDeleteSection(section)}
              >
                Xóa cột
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>

      {/*  KHÔNG tô nền / viền cột đích khi kéo qua: thẻ đang kéo đã được dời hẳn
          vào cột này rồi (xem `displayed` ở `kanban-board.tsx`), đó mới là dấu hiệu
          rõ nhất. Tô thêm một mảng xanh mờ chỉ làm cả cột nhấp nháy. */}
      <div ref={setNodeRef} className="flex min-h-24 flex-1 flex-col gap-2 px-2 pb-2">
        <SortableContext items={items} strategy={verticalListSortingStrategy}>
          {tasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              labelFields={labelFields}
              fields={fields}
              canEdit={canEdit}
              onToggleDone={onToggleDone}
              onOpen={onOpenTask}
              dragDisabled={dragDisabled || !canEdit}
              hideGhost={task.id === hideGhostTaskId}
            />
          ))}
        </SortableContext>

        {canEdit &&
          (adding ? (
            <Input
              autoFocus
              value={title}
              placeholder="Tên việc rồi Enter"
              onChange={(e) => setTitle(e.target.value)}
              onBlur={saveNewTask}
              onKeyDown={(e) => {
                if (e.key === 'Enter') saveNewTask()
                if (e.key === 'Escape') setAdding(false)
              }}
            />
          ) : (
            <Button
              variant="ghost"
              size="sm"
              className="justify-start text-muted-foreground"
              onClick={() => setAdding(true)}
            >
              <Plus className="size-4" />
              Thêm việc
            </Button>
          ))}
      </div>
    </div>
  )
}
