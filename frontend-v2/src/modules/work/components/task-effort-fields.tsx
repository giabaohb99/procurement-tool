import { Clock, Shapes, Timer } from 'lucide-react'
import { useState } from 'react'

import { Input } from '@/shared/ui/input'
import { useActiveTaskTypes } from '../hooks/use-task-types'
import type { WorkTask } from '../types/work'
import { formatHours, parseHours } from '../utils/effort-hours'
import { TaskChipSelect } from './task-chip-select'
import { TaskDetailRow } from './task-detail-row'

interface TaskEffortFieldsProps {
  task: WorkTask
  /** Việc đã xong — chỉ lúc này mới nhập được giờ thực tế (máy chủ cũng chặn). */
  done: boolean
  canEdit: boolean
  onSave: (values: Record<string, unknown>) => void
}

/**
 * Ba hàng «Loại việc · Ước lượng · Thực tế» của panel chi tiết (duoc-CR-656). Lưu khi rời ô như mọi ô khác.
 *
 * Ô giờ giữ BẢN NHÁP cục bộ và dựng lại khi giá trị máy chủ đổi (`key` chứa giá trị), nên làm mới nền không
 * ghi đè chữ đang gõ giữa chừng; gõ sai (chữ, quá 999) thì trả về giá trị cũ và báo đỏ chứ không lưu bừa.
 */
export function TaskEffortFields({ task, done, canEdit, onSave }: TaskEffortFieldsProps) {
  const { data: types = [] } = useActiveTaskTypes()
  //  Loại của việc cũ có thể đã bị ngừng dùng → không có trong danh sách chọn; vẫn phải hiện tên đang gán.
  const options = types.map((t) => ({ value: String(t.id), label: t.name }))
  if (task.task_type_id && !options.some((o) => o.value === String(task.task_type_id))) {
    options.push({ value: String(task.task_type_id), label: task.task_type_name || `#${task.task_type_id}` })
  }

  return (
    <>
      <TaskDetailRow icon={Shapes} label="Loại việc">
        <TaskChipSelect
          ariaLabel="Loại việc"
          variant="dot"
          placeholder="Chưa chọn loại"
          value={task.task_type_id ? String(task.task_type_id) : ''}
          options={options}
          disabled={!canEdit}
          onChange={(v) => onSave({ task_type_id: Number(v) })}
        />
      </TaskDetailRow>

      <TaskDetailRow icon={Clock} label="Ước lượng (giờ)">
        <HoursInput
          key={`est-${task.id}-${task.estimate_hours ?? ''}`}
          label="Ước lượng (giờ)"
          value={task.estimate_hours}
          canEdit={canEdit}
          onCommit={(v) => onSave({ estimate_hours: v })}
        />
      </TaskDetailRow>

      <TaskDetailRow icon={Timer} label="Thực tế (giờ)">
        {done ? (
          <HoursInput
            key={`act-${task.id}-${task.actual_hours ?? ''}`}
            label="Thực tế (giờ)"
            value={task.actual_hours}
            canEdit={canEdit}
            //  Nhắc nhẹ — KHÔNG bắt buộc (Q13): số chính của báo cáo là thời gian trôi qua.
            hint={task.actual_hours === null ? 'Nhập nếu nhớ — không bắt buộc' : undefined}
            onCommit={(v) => onSave({ actual_hours: v })}
          />
        ) : (
          <span className="px-1.5 text-sm text-muted-foreground">Nhập được khi công việc đã hoàn thành</span>
        )}
      </TaskDetailRow>
    </>
  )
}

interface HoursInputProps {
  label: string
  value: string | null
  canEdit: boolean
  hint?: string
  onCommit: (hours: string) => void
}

function HoursInput({ label, value, canEdit, hint, onCommit }: HoursInputProps) {
  const [draft, setDraft] = useState(formatHours(value))
  const parsed = parseHours(draft)
  const invalid = parsed === null

  //  Chỉ xem: hiện CHỮ, không `<Input disabled>` (ô disabled không bôi đen/copy được).
  if (!canEdit) {
    return <span className="px-1.5 text-sm">{draft ? `${draft} giờ` : '—'}</span>
  }

  return (
    <div className="flex items-center gap-2">
      <Input
        value={draft}
        inputMode="decimal"
        aria-label={label}
        aria-invalid={invalid}
        placeholder={hint ?? '0'}
        onChange={(e) => setDraft(e.target.value)}
        //  Enter chốt ô bằng cách rời ô; panel không nằm trong <form> nhưng giữ cho đồng bộ với các ô khác.
        onKeyDown={(e) => e.key === 'Enter' && e.currentTarget.blur()}
        onBlur={() => {
          if (parsed === null) return setDraft(formatHours(value)) // sai → trả về giá trị đang lưu
          if (parsed !== (value === null ? '0' : String(Number(value)))) onCommit(parsed)
        }}
        className="h-7 w-28 text-sm"
      />
      <span className="text-xs text-muted-foreground">giờ</span>
    </div>
  )
}
