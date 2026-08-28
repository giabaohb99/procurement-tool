import { Trash2 } from 'lucide-react'

import { AuditTimeline } from '@/shared/audit'
import { Button } from '@/shared/ui/button'
import { DatePicker } from '@/shared/ui/date-picker'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/shared/ui/sheet'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import {
  useCreateSubtask,
  useDeleteTask,
  useSetAssignees,
  useSetTaskLabel,
  useSetTaskTags,
  useUpdateTask,
  useWorkTask,
} from '../hooks/use-work-board'
import { useWorkLabelFields, useWorkMembers, useWorkTags } from '../hooks/use-work-config'
import type { WorkSection } from '../types/work'
import { WORK_PRIORITY_LABELS, WORK_TASK_STATUS } from '../types/work'
import { addDays } from '../utils/due-date'
import { chipClass } from '../utils/work-colors'
import { TaskSubtaskList } from './task-subtask-list'
import { LabelFieldInput } from './label-field-input'
import { TaskDescriptionField, TaskTitleField } from './task-text-fields'

interface TaskDetailSheetProps {
  taskId: number | null
  listId: number
  sections: WorkSection[]
  canEdit: boolean
  onClose: () => void
}

/**
 * Panel chi tiết một việc (D-03), trượt từ phải — thứ tự hàng bám §6 của
 * `05-giao-dien.md`: tiêu đề → người phụ trách → hạn → cột → nhãn → mô tả →
 * việc con → nhật ký.
 *
 * Mọi ô LƯU KHI RỜI Ô (blur), không có nút Lưu: đây là panel thao tác nhanh
 * cạnh bảng, bắt bấm Lưu cho từng ô thì thao tác nào cũng hai nhịp.
 *
 * ⚠️ CHƯA có khối bình luận (E-01) — thuộc W3, cùng đợt với thông báo.
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
  const { data: tags = [] } = useWorkTags(listId)
  const { data: labelFields = [] } = useWorkLabelFields(listId)

  const updateTask = useUpdateTask(listId)
  const deleteTask = useDeleteTask(listId)
  const createSubtask = useCreateSubtask(listId)
  const setAssignees = useSetAssignees(listId)
  const setTags = useSetTaskTags(listId)
  const setLabel = useSetTaskLabel(listId)

  function save(values: Record<string, unknown>) {
    if (!taskId) return
    updateTask.mutate({ id: taskId, values })
  }

  const isDone = task?.status === WORK_TASK_STATUS.DONE

  return (
    <Sheet open={taskId !== null} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="w-full gap-0 overflow-y-auto sm:max-w-xl">
        <SheetHeader>
          <SheetTitle className="sr-only">Chi tiết công việc</SheetTitle>
        </SheetHeader>

        {isLoading || !task ? (
          <div className="space-y-3 p-6">
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-24 w-full" />
          </div>
        ) : (
          <div className="space-y-5 p-6 pt-0">
            <div className="flex items-start gap-2">
              <TaskTitleField
                key={`title-${task.id}`}
                title={task.title}
                canEdit={canEdit}
                strike={isDone}
                onSave={(title) => save({ title })}
              />
              {canEdit && (
                <Button
                  variant="ghost"
                  size="icon"
                  title="Xóa công việc"
                  onClick={() => {
                    deleteTask.mutate(task.id)
                    onClose()
                  }}
                >
                  <Trash2 className="size-4 text-destructive" />
                </Button>
              )}
            </div>

            <Row label="Trạng thái">
              <Select
                value={String(task.status)}
                disabled={!canEdit}
                onValueChange={(v) => save({ status: Number(v) })}
              >
                <SelectTrigger size="sm" className="w-44">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">Đang mở</SelectItem>
                  <SelectItem value="2">Hoàn thành</SelectItem>
                  <SelectItem value="3">Đã hủy</SelectItem>
                </SelectContent>
              </Select>
            </Row>

            <Row label="Người phụ trách">
              <div className="flex flex-wrap gap-1">
                {members.map((m) => {
                  const chosen = task.assignees.some(
                    (a) => a.employee_id === m.employee_id && a.kind === 1,
                  )
                  return (
                    <button
                      key={m.id}
                      type="button"
                      disabled={!canEdit}
                      onClick={() => {
                        const current = task.assignees
                          .filter((a) => a.kind === 1)
                          .map((a) => a.employee_id)
                        const next = chosen
                          ? current.filter((id) => id !== m.employee_id)
                          : [...current, m.employee_id]
                        setAssignees.mutate({ taskId: task.id, picIds: next })
                      }}
                      className={cn(
                        'rounded-full border px-2 py-0.5 text-xs',
                        chosen
                          ? 'border-primary bg-primary/10 font-medium text-primary'
                          : 'text-muted-foreground',
                      )}
                    >
                      {m.employee_name || `#${m.employee_id}`}
                    </button>
                  )
                })}
                {members.length === 0 && (
                  <span className="text-sm text-muted-foreground">
                    Chưa có thành viên nào trong danh sách
                  </span>
                )}
              </div>
            </Row>

            <Row label="Hạn chót">
              <div className="flex flex-wrap items-center gap-2">
                <DatePicker
                  size="sm"
                  clearable
                  value={task.due_date}
                  disabled={!canEdit}
                  onChange={(v) => save({ due_date: v })}
                />
                {canEdit && (
                  <>
                    <Button variant="outline" size="sm" onClick={() => save({ due_date: addDays(0) })}>
                      Hôm nay
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => save({ due_date: addDays(1) })}>
                      Ngày mai
                    </Button>
                  </>
                )}
              </div>
            </Row>

            <Row label="Ngày bắt đầu">
              <DatePicker
                size="sm"
                clearable
                value={task.start_date}
                disabled={!canEdit}
                onChange={(v) => save({ start_date: v })}
              />
            </Row>

            <Row label="Cột">
              <Select
                value={task.section_id ? String(task.section_id) : ''}
                disabled={!canEdit}
                onValueChange={(v) => save({ section_id: Number(v) })}
              >
                <SelectTrigger size="sm" className="w-44">
                  <SelectValue placeholder="Chưa thuộc cột nào" />
                </SelectTrigger>
                <SelectContent>
                  {sections.map((s) => (
                    <SelectItem key={s.id} value={String(s.id)}>
                      {s.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Row>

            <Row label="Độ ưu tiên">
              <Select
                value={String(task.priority)}
                disabled={!canEdit}
                onValueChange={(v) => save({ priority: Number(v) })}
              >
                <SelectTrigger size="sm" className="w-44">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(WORK_PRIORITY_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Row>

            <Row label="Tag">
              <div className="flex flex-wrap gap-1">
                {tags.map((t) => {
                  const chosen = task.tag_ids.includes(t.id)
                  return (
                    <button
                      key={t.id}
                      type="button"
                      disabled={!canEdit}
                      onClick={() =>
                        setTags.mutate({
                          taskId: task.id,
                          tagIds: chosen
                            ? task.tag_ids.filter((id) => id !== t.id)
                            : [...task.tag_ids, t.id],
                        })
                      }
                      className={cn(
                        'rounded px-1.5 py-0.5 text-xs',
                        chipClass(t.color),
                        !chosen && 'opacity-40',
                      )}
                    >
                      {t.name}
                    </button>
                  )
                })}
                {tags.length === 0 && (
                  <span className="text-sm text-muted-foreground">Danh sách chưa khai tag</span>
                )}
              </div>
            </Row>

            {labelFields.map((f) => (
              <Row key={f.id} label={f.name}>
                <LabelFieldInput
                  field={f}
                  values={task.labels.filter((l) => l.field_id === f.id)}
                  members={members}
                  disabled={!canEdit}
                  onChange={(value) =>
                    setLabel.mutate({ taskId: task.id, fieldId: f.id, value })
                  }
                />
              </Row>
            ))}

            <TaskDescriptionField
              key={`desc-${task.id}`}
              description={task.description}
              canEdit={canEdit}
              onSave={(description) => save({ description })}
            />

            <TaskSubtaskList
              subtasks={task.subtasks ?? []}
              canEdit={canEdit}
              onAdd={(title) => createSubtask.mutate({ taskId: task.id, title })}
              onToggle={(subtaskId, done) =>
                updateTask.mutate({
                  id: subtaskId,
                  values: { status: done ? WORK_TASK_STATUS.DONE : WORK_TASK_STATUS.OPEN },
                })
              }
            />

            <AuditTimeline entity="work_task" entityId={task.id} showMessage dense />
          </div>
        )}
      </SheetContent>
    </Sheet>
  )
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[7rem_1fr] items-start gap-3">
      <span className="pt-1 text-xs text-muted-foreground">{label}</span>
      <div>{children}</div>
    </div>
  )
}
