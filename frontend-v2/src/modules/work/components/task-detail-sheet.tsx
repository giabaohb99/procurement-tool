import {
  AlignLeft,
  CircleDot,
  Columns3,
  ListTodo,
  Trash2,
  User,
  X,
} from 'lucide-react'
import { useMemo } from 'react'

import { AuditTimeline } from '@/shared/audit'
import { Button } from '@/shared/ui/button'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { Sheet, SheetClose, SheetContent, SheetHeader, SheetTitle } from '@/shared/ui/sheet'
import { Skeleton } from '@/shared/ui/skeleton'
import {
  useCreateSubtask,
  useDeleteTask,
  useSetAssignees,
  useSetTaskLabel,
  useToggleSubtask,
  useUpdateTask,
  useWorkTask,
} from '../hooks/use-work-board'
import { useWorkLabelFields, useWorkMembers } from '../hooks/use-work-config'
import type { WorkSection } from '../types/work'
import { WORK_TASK_STATUS } from '../types/work'
import { LabelFieldInput } from './label-field-input'
import { TaskAssigneePicker } from './task-assignee-picker'
import { TaskChipSelect } from './task-chip-select'
import { TaskDateRow } from './task-date-row'
import { TaskDetailRow } from './task-detail-row'
import { TaskStatusSelect } from './task-status-select'
import { TaskSubtaskList } from './task-subtask-list'
import { TaskDescriptionField } from './task-description-field'
import { TaskTitleField } from './task-title-field'

interface TaskDetailSheetProps {
  taskId: number | null
  listId: number
  sections: WorkSection[]
  canEdit: boolean
  onClose: () => void
}

/**
 * Panel chi tiết một việc (D-03), trượt từ phải — dựng theo panel của Lark:
 * thanh trên cùng giữ TRẠNG THÁI cùng các nút thao tác, dưới là tiêu đề rồi
 * đến các hàng thuộc tính `biểu tượng · [tên trường] · giá trị`, cuối cùng là
 * khối nhật ký trên nền xám.
 *
 * Thứ tự hàng vẫn bám §6 của `05-giao-dien.md`: người phụ trách → thời gian →
 * cột → trường tùy biến (Tag, Độ ưu tiên…) → mô tả → việc con → nhật ký.
 *
 * Mọi ô LƯU KHI RỜI Ô (blur), không có nút Lưu: đây là panel thao tác nhanh
 * cạnh bảng, bắt bấm Lưu cho từng ô thì thao tác nào cũng hai nhịp.
 *
 * ⚠️ CHƯA có khối bình luận (E-01) — thuộc W3, cùng đợt với thông báo. Chỗ của
 * nó là ngay trên `AuditTimeline`, trong cùng khối nền xám.
 */
export function TaskDetailSheet({
  taskId,
  listId,
  sections,
  canEdit,
  onClose,
}: TaskDetailSheetProps) {
  const { data: task, isLoading } = useWorkTask(taskId ?? undefined)
  const { data: members = [] } = useWorkMembers(listId)
  const { data: labelFields = [] } = useWorkLabelFields(listId)

  const updateTask = useUpdateTask(listId)
  const deleteTask = useDeleteTask(listId)
  const createSubtask = useCreateSubtask(listId)
  const setAssignees = useSetAssignees(listId)
  const setLabel = useSetTaskLabel(listId)
  const toggleSubtask = useToggleSubtask(listId)

  const sectionOptions = useMemo(
    () => sections.map((s) => ({ value: String(s.id), label: s.name, color: s.color })),
    [sections],
  )

  function save(values: Record<string, unknown>) {
    if (!taskId) return
    updateTask.mutate({ id: taskId, values })
  }

  const isDone = task?.status === WORK_TASK_STATUS.DONE

  return (
    <Sheet open={taskId !== null} onOpenChange={(open) => !open && onClose()}>
      {/*  Nút đóng mặc định của `SheetContent` nằm đè lên thanh trên cùng nên
           tắt đi, dựng lại trong thanh cho thẳng hàng với nút Xóa. */}
      <SheetContent
        showCloseButton={false}
        className="flex w-full flex-col gap-0 p-0 sm:max-w-xl"
      >
        <SheetHeader className="flex-row items-center justify-between gap-2 border-b px-4 py-2.5">
          <SheetTitle className="sr-only">Chi tiết công việc</SheetTitle>
          {task ? (
            <TaskStatusSelect
              status={task.status}
              disabled={!canEdit}
              onChange={(status) => save({ status })}
            />
          ) : (
            <span />
          )}
          <div className="flex items-center gap-1">
            {canEdit && task && (
              <IconTooltip label="Xóa công việc">
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-8"
                  aria-label="Xóa công việc"
                  onClick={() => {
                    deleteTask.mutate(task.id)
                    onClose()
                  }}
                >
                  <Trash2 className="size-4 text-destructive" />
                </Button>
              </IconTooltip>
            )}
            <IconTooltip label="Đóng">
              <SheetClose asChild>
                <Button variant="ghost" size="icon" className="size-8" aria-label="Đóng">
                  <X className="size-4" />
                </Button>
              </SheetClose>
            </IconTooltip>
          </div>
        </SheetHeader>

        {isLoading || !task ? (
          <div className="space-y-3 p-4">
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-24 w-full" />
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto">
            <div className="space-y-0.5 px-4 py-3">
              <TaskTitleField
                key={`title-${task.id}`}
                title={task.title}
                canEdit={canEdit}
                strike={isDone}
                onSave={(title) => save({ title })}
              />

              <TaskDetailRow icon={User} srLabel="Người phụ trách">
                <TaskAssigneePicker
                  assignees={task.assignees}
                  members={members}
                  disabled={!canEdit}
                  onChange={(picIds) => setAssignees.mutate({ taskId: task.id, picIds })}
                />
              </TaskDetailRow>

              <TaskDateRow
                startDate={task.start_date}
                dueDate={task.due_date}
                done={isDone}
                canEdit={canEdit}
                onChange={save}
              />

              <TaskDetailRow icon={Columns3} label="Cột">
                <TaskChipSelect
                  ariaLabel="Cột"
                  variant="dot"
                  placeholder="Chưa thuộc cột nào"
                  value={task.section_id ? String(task.section_id) : ''}
                  options={sectionOptions}
                  disabled={!canEdit}
                  onChange={(v) => save({ section_id: Number(v) })}
                />
              </TaskDetailRow>


              {labelFields.map((f) => (
                <TaskDetailRow key={f.id} icon={CircleDot} label={f.name}>
                  <LabelFieldInput
                    field={f}
                    values={task.labels.filter((l) => l.field_id === f.id)}
                    members={members}
                    disabled={!canEdit}
                    onChange={(value) => setLabel.mutate({ taskId: task.id, fieldId: f.id, value })}
                  />
                </TaskDetailRow>
              ))}

              <TaskDetailRow icon={AlignLeft} srLabel="Mô tả">
                <TaskDescriptionField
                  key={`desc-${task.id}`}
                  description={task.description}
                  canEdit={canEdit}
                  onSave={(description) => save({ description })}
                />
              </TaskDetailRow>

              <TaskDetailRow icon={ListTodo} srLabel="Việc con" className="items-start">
                <TaskSubtaskList
                  subtasks={task.subtasks ?? []}
                  canEdit={canEdit}
                  onAdd={(title) => createSubtask.mutate({ taskId: task.id, title })}
                  onToggle={(subtaskId, done) =>
                    toggleSubtask.mutate({ parentId: task.id, subtaskId, done })
                  }
                />
              </TaskDetailRow>
            </div>

            {/*  Nhật ký tách hẳn xuống nền xám như khối bình luận của Lark: nó
                 là chuyện ĐÃ xảy ra, không phải thuộc tính sửa được, nên đứng
                 lẫn trong dải hàng ở trên là đọc nhầm. Không thêm tiêu đề nào
                 ở đây — `AuditTimeline` đã tự mang tiêu đề «Lịch sử thao tác». */}
            <section className="border-t bg-muted/30 px-4 py-3">
              <AuditTimeline entity="work_task" entityId={task.id} showMessage dense />
            </section>
          </div>
        )}
      </SheetContent>
    </Sheet>
  )
}

