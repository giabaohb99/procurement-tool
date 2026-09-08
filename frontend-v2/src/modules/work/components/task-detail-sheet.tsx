import {
  AlignLeft,
  CircleDot,
  Columns3,
  Diamond,
  ListTodo,
  Paperclip,
  Trash2,
  User,
  X,
} from 'lucide-react'
import { useMemo } from 'react'

import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
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
import { WORK_TASK_KIND, WORK_TASK_STATUS } from '../types/work'
import { LabelFieldInput } from './label-field-input'
import { TaskAttachments } from './task-attachments'
import { TaskComments, TaskCommentComposer } from './task-comments'
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
 * khối bình luận trên nền xám.
 *
 * Thứ tự hàng vẫn bám §6 của `05-giao-dien.md`: người phụ trách → thời gian →
 * cột → trường tùy biến (Tag, Độ ưu tiên…) → mô tả → việc con → đính kèm, rồi
 * tới khối bình luận.
 *
 * Mọi ô LƯU KHI RỜI Ô (blur), không có nút Lưu: đây là panel thao tác nhanh
 * cạnh bảng, bắt bấm Lưu cho từng ô thì thao tác nào cũng hai nhịp.
 *
 * Bình luận (E-01) và đính kèm (E-03) KHÔNG có bảng riêng của phân hệ này: cả
 * hai dùng hạ tầng chung của hệ (`tab_comment`, `tab_file_link`) với
 * `entity = "work_task"` — xem `api/task-support-api.ts`. Đính kèm là một hàng
 * thuộc tính như mọi hàng khác; bình luận nằm trong mảng nền xám cuối panel.
 *
 * ⚠️ Panel KHÔNG có khối «Lịch sử thao tác» (bỏ 03/09/2026): nhật ký của việc
 * nay đọc ở tab **Hoạt động** cấp dự án (D-09), nơi gộp đủ mọi việc và mỗi dòng
 * bấm được sang đúng việc. Đừng gắn `AuditTimeline` lại vào đây.
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
      <SheetContent showCloseButton={false} className="flex w-full flex-col gap-0 p-0 sm:max-w-xl">
        <SheetHeader className="flex-row items-center justify-between gap-2 border-b px-4 py-2.5">
          <SheetTitle className="sr-only">Chi tiết công việc</SheetTitle>
          {task ? (
            <div className="flex items-center gap-1.5">
              <TaskStatusSelect
                status={task.status}
                disabled={!canEdit}
                onChange={(status) => save({ status })}
              />
              {/*  Bật/tắt CỘT MỐC (B-14). Đặt cạnh trạng thái vì cùng loại: cả
                   hai đều nói "việc này là loại gì", và cùng là thứ đọc trước
                   khi đọc nội dung. Chỉ xem thì chỉ hiện khi ĐANG là cột mốc —
                   một nút chết cạnh mọi việc thường thì chỉ tổ gây hỏi. */}
              {(canEdit || task.kind === WORK_TASK_KIND.MILESTONE) && (
                <Button
                  variant={task.kind === WORK_TASK_KIND.MILESTONE ? 'secondary' : 'ghost'}
                  size="sm"
                  className="h-7 gap-1.5 rounded-full px-2.5 text-xs"
                  disabled={!canEdit}
                  aria-pressed={task.kind === WORK_TASK_KIND.MILESTONE}
                  title="Cột mốc chỉ có MỘT ngày (hạn) và hiện thành hình thoi trên Gantt"
                  onClick={() =>
                    save({
                      kind:
                        task.kind === WORK_TASK_KIND.MILESTONE
                          ? WORK_TASK_KIND.TASK
                          : WORK_TASK_KIND.MILESTONE,
                    })
                  }
                >
                  <Diamond
                    className={cn(
                      'size-3.5',
                      task.kind === WORK_TASK_KIND.MILESTONE && 'fill-current',
                    )}
                  />
                  Cột mốc
                </Button>
              )}
            </div>
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
          <>
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
                      onChange={(value) =>
                        setLabel.mutate({ taskId: task.id, fieldId: f.id, value })
                      }
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

                <TaskDetailRow icon={Paperclip} srLabel="Đính kèm" className="items-start">
                  <TaskAttachments taskId={task.id} canEdit={canEdit} />
                </TaskDetailRow>
              </div>

              {/*  Bình luận tách hẳn xuống nền xám như panel của Lark: nó là
                 TRAO ĐỔI, không phải thuộc tính sửa được, nên đứng lẫn trong
                 dải hàng ở trên là đọc nhầm.

                 ⚠️ KHÔNG còn khối «Lịch sử thao tác» ở đây (bỏ 03/09/2026 theo
                 yêu cầu khách). Nhật ký của việc nay đọc ở tab **Hoạt động** cấp
                 dự án (D-09) — nó gộp đủ mọi việc trong dự án và mỗi dòng bấm
                 được sang đúng việc, nên để thêm một bản rút gọn ở đây là hai
                 chỗ nói cùng một chuyện, mà panel thì đã dài. */}
              <div className="border-t bg-muted/30 px-4 py-3">
                <TaskComments taskId={task.id} listId={listId} />
              </div>
            </div>

            {/*  Ô soạn GHIM ĐÁY panel, nằm NGOÀI vùng cuộn — đúng lối Lark.
                 Để nó trôi trong luồng cuộn thì với việc đã bàn vài chục lượt,
                 muốn góp một câu phải cuộn qua hết nhật ký mới thấy ô nhập; mà
                 gửi xong danh sách dài thêm, nó lại tụt xuống dưới tầm nhìn.
                 Khách xem không có ô này (backend cũng chặn, xem `resolve_doc`). */}
            {canEdit && (
              <div className="shrink-0 border-t bg-muted/30 px-4 py-2">
                <TaskCommentComposer taskId={task.id} listId={listId} />
              </div>
            )}
          </>
        )}
      </SheetContent>
    </Sheet>
  )
}
