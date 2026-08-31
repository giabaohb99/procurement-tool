import { useEffect, useRef, useState } from 'react'

import { Checkbox } from '@/shared/ui/checkbox'
import { Input } from '@/shared/ui/input'
import { columnWidthVar } from '../hooks/use-list-column-widths'
import { ROW_PAD_LEFT } from '../utils/list-metrics'
import type { WorkLabelField, WorkMember } from '../types/work'
import { WORK_ASSIGNEE_KIND } from '../types/work'
import { toDraftLabelValues } from '../utils/draft-label-value'
import { TITLE_COLUMN, type TaskListColumn } from '../utils/list-columns'
import { LabelFieldInput } from './label-field-input'
import { TaskAssigneePicker } from './task-assignee-picker'
import { TaskDueCell } from './task-due-cell'

/** Việc đang soạn — mọi thứ gán ngay trên dòng, gửi đi một lượt khi bấm Enter. */
export interface NewTaskDraft {
  title: string
  dueDate: string
  /** Ngày bắt đầu — cột `start`, chỉ gửi đi khi người dùng thực sự chọn. */
  startDate: string
  picIds: number[]
  /** Khóa là `field_id`; giá trị thô đa hình đúng như `LabelFieldInput` trả ra. */
  labels: Record<number, unknown>
}

interface TaskDraftRowProps {
  columns: TaskListColumn[]
  members: WorkMember[]
  /**
   * Nhân sự của người đang đăng nhập — gán SẴN làm người phụ trách.
   *
   * Đại đa số việc tự thêm là việc của chính mình, nên để trống thì gần như lần
   * nào cũng phải bấm thêm một nhịp. Vẫn gỡ ra được ngay trên dòng. `undefined`
   * khi tài khoản chưa nối nhân sự, hoặc người đó không phải thành viên dự án —
   * gán một người ngoài dự án thì họ không mở nổi việc để biết mình bị gán.
   */
  defaultPicId?: number
  /** Chiều cao CỐ ĐỊNH của dòng (px) — chỉ Gantt truyền, xem `TaskListRow`. */
  rowHeight?: number
  onSave: (draft: NewTaskDraft) => void
  onCancel: () => void
}

function emptyDraft(defaultPicId?: number): NewTaskDraft {
  return {
    title: '',
    dueDate: '',
    startDate: '',
    picIds: defaultPicId ? [defaultPicId] : [],
    labels: {},
  }
}

/**
 * Dòng SOẠN việc mới — nguyên một dòng gán được mọi trường, không phải mỗi ô tên.
 *
 * Bản đầu chỉ có ô nhập tên: gõ xong Enter rồi phải mở panel chi tiết để gán
 * người và hạn, tức là ba thao tác cho một việc. Ở đây các ô y hệt dòng thật —
 * dùng lại đúng những component ấy — nên gán trước rồi Enter một phát là xong.
 *
 * Trường tùy biến giữ ở dạng THÔ (`labels`) chứ không dịch sang payload ngay:
 * API tạo task không nhận nhãn, chúng phải gửi bằng các lượt gọi riêng SAU khi
 * có `task_id`; dịch sớm thì phải dịch ngược lại để vẽ ô, hỏng hai lần.
 */
export function TaskDraftRow({
  columns,
  members,
  defaultPicId,
  rowHeight,
  onSave,
  onCancel,
}: TaskDraftRowProps) {
  const [draft, setDraft] = useState<NewTaskDraft>(() => emptyDraft(defaultPicId))
  const rowRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const dirty = draft.title.trim() !== ''

  /*  Bấm ra ngoài thì đóng dòng nháp — nhưng CHỈ khi chưa gõ gì. Đang gõ dở mà
      lỡ bấm ra ngoài lại mất trắng thì tệ hơn hẳn việc để thừa một dòng.

      Hai chỗ phải chừa ra: chính dòng này, và các popover của Radix (ô chọn
      người / lịch / tag) — chúng render sang portal ở cuối `body` nên xét theo
      cây DOM là "bên ngoài", không chừa thì mở lịch phát nào dòng đóng phát ấy.  */
  useEffect(() => {
    function handlePointerDown(event: PointerEvent) {
      if (dirty) return
      const target = event.target
      if (!(target instanceof Node)) return
      if (rowRef.current?.contains(target)) return
      if (target instanceof Element && target.closest('[data-radix-popper-content-wrapper]')) return
      onCancel()
    }
    document.addEventListener('pointerdown', handlePointerDown)
    return () => document.removeEventListener('pointerdown', handlePointerDown)
  }, [dirty, onCancel])

  function patch(values: Partial<NewTaskDraft>) {
    setDraft((prev) => ({ ...prev, ...values }))
  }

  function save() {
    const title = draft.title.trim()
    //  Tên rỗng = bỏ cuộc, không tạo việc "chưa đặt tên" rồi bắt người dùng đi
    //  dọn. Mọi thứ đã gán cũng bỏ theo.
    if (!title) {
      onCancel()
      return
    }
    onSave({ ...draft, title })
    //  Dòng nháp Ở LẠI để gõ tiếp việc kế — thêm việc hiếm khi đi một cái, đóng
    //  sau mỗi lần Enter thì cứ mỗi việc lại phải rê chuột xuống bấm «Việc mới».
    //  Chỉ ô tên được dọn; người phụ trách / hạn / nhãn vừa chọn giữ nguyên vì
    //  mấy việc thêm liền nhau thường cùng một bộ.
    setDraft((prev) => ({ ...prev, title: '' }))
    inputRef.current?.focus()
  }

  return (
    <div
      ref={rowRef}
      style={{ paddingLeft: ROW_PAD_LEFT, height: rowHeight }}
      className="flex items-center gap-1.5 border-b border-border/60 bg-accent/30 py-1.5 pr-2"
    >
      {/*  Ô tên rộng đúng bằng cột tên của dòng thật (`--wcol-title`) rồi tới
           khoảng đệm co giãn — có thế các ô còn lại mới thẳng hàng với dòng
           trên khi người dùng kéo giãn cột tên. */}
      <div
        className="flex min-w-0 shrink-0 items-center gap-1.5"
        style={{ width: `var(${columnWidthVar(TITLE_COLUMN.key)})` }}
      >
        <span className="w-[18px] shrink-0" aria-hidden />
        <Checkbox disabled className="shrink-0 rounded-full" aria-hidden tabIndex={-1} />

        <Input
          autoFocus
          ref={inputRef}
          value={draft.title}
          aria-label="Tên công việc mới"
          placeholder="Tên công việc rồi Enter"
          /*  Không viền, không vòng sáng: cả DÒNG đã đổi nền để nói "đang soạn",
              thêm một cái hộp viền vàng quanh ô tên nữa thì nó là khung trong
              khung, mà các ô còn lại của dòng đều không có viền — nhìn lệch hẳn.
              `dark:bg-transparent` vì `Input` gốc có `dark:bg-input/30`, để
              nguyên là nền tối lại hiện đúng cái hộp vừa bỏ. */
          className="h-6 min-w-0 flex-1 border-0 bg-transparent px-1 py-0 text-sm shadow-none focus-visible:ring-0 dark:bg-transparent"
          onChange={(e) => patch({ title: e.target.value })}
          onKeyDown={(e) => {
            if (e.key === 'Enter') save()
            if (e.key === 'Escape') onCancel()
          }}
        />
      </div>

      <span className="min-w-0 flex-1" aria-hidden />

      {columns.map((col) => (
        <div key={col.key} className="shrink-0" style={{ width: `var(${columnWidthVar(col.key)})` }}>
          <DraftCell
            column={col}
            draft={draft}
            members={members}
            onPatch={patch}
            onPatchLabel={(fieldId, value) =>
              patch({ labels: { ...draft.labels, [fieldId]: value } })
            }
          />
        </div>
      ))}
    </div>
  )
}

interface DraftCellProps {
  column: TaskListColumn
  draft: NewTaskDraft
  members: WorkMember[]
  onPatch: (values: Partial<NewTaskDraft>) => void
  onPatchLabel: (fieldId: number, value: unknown) => void
}

function DraftCell({ column, draft, members, onPatch, onPatchLabel }: DraftCellProps) {
  if (column.key === 'assignees') {
    //  `TaskAssigneePicker` đọc `WorkAssignee[]` của máy chủ; việc chưa tồn tại
    //  nên dựng tạm từ danh sách thành viên để chip hiện đúng tên.
    const assignees = draft.picIds.map((id) => {
      const member = members.find((m) => m.employee_id === id)
      return {
        employee_id: id,
        kind: WORK_ASSIGNEE_KIND.PIC,
        employee_name: member?.employee_name ?? '',
        employee_code: member?.employee_code ?? '',
      }
    })
    return (
      <TaskAssigneePicker
        compact
        assignees={assignees}
        members={members}
        onChange={(picIds) => onPatch({ picIds })}
      />
    )
  }

  if (column.key === 'due') {
    return (
      <TaskDueCell
        dueDate={draft.dueDate}
        done={false}
        canEdit
        onChange={(dueDate) => onPatch({ dueDate })}
      />
    )
  }

  if (column.key === 'start') {
    return (
      <TaskDueCell
        label="Ngày bắt đầu"
        tone={false}
        dueDate={draft.startDate}
        done={false}
        canEdit
        onChange={(startDate) => onPatch({ startDate })}
      />
    )
  }

  //  Cột TRẠNG THÁI cố ý để trống ở dòng nháp: việc chưa tồn tại thì trạng thái
  //  duy nhất có nghĩa là «Đang mở», bày một ô chọn ra chỉ mời người ta tạo sẵn
  //  một việc «Hoàn thành».
  if (column.key === 'status') return null

  const field: WorkLabelField | undefined = column.field
  if (!field) return null
  return (
    <LabelFieldInput
      compact
      field={field}
      values={toDraftLabelValues(field, draft.labels[field.id], members)}
      members={members}
      onChange={(value) => onPatchLabel(field.id, value)}
    />
  )
}
