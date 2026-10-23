import { Sparkles, Trash2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { MultiPicker } from '@/shared/ui/multi-picker'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'
import { AI_PLAN_PRIORITIES, type AiPlanAssignee, type AiPlanTaskType } from '../types/ai-plan'
import type { EditableSubtask } from '../utils/ai-plan-edit'

/** Ô «Loại việc» để trống. Không dùng `0` / chuỗi rỗng: Radix Select cấm giá trị rỗng. */
const NO_TYPE = 'none'

export interface AiPlanPersonOption extends AiPlanAssignee {
  /** Có trong danh bạ đang làm — người đã nghỉ chỉ còn trong kế hoạch cũ thì `false`. */
  active: boolean
}

interface AiPlanRowEditorProps {
  row: EditableSubtask
  /** Việc con: gọn hơn — bỏ mô tả, tiêu chí, lý do chọn người. */
  compact?: boolean
  readOnly: boolean
  people: AiPlanPersonOption[]
  taskTypes: AiPlanTaskType[]
  problems: string[]
  onChange: (patch: Partial<Omit<EditableSubtask, 'uid'>>) => void
  onRemove: () => void
  children?: React.ReactNode
}

function parseHours(raw: string): number | null {
  const text = raw.trim().replace(',', '.')
  if (!text) return null
  const value = Number(text)
  //  Giữ cả số sai (âm, 0, quá 999) để `findLocalProblems` báo đỏ ngay dòng này,
  //  không lặng lẽ đổi thành rỗng làm người nhập tưởng đã lưu được.
  return Number.isFinite(value) ? value : Number.NaN
}

/**
 * Một dòng việc (hoặc việc con) của kế hoạch AI — người duyệt sửa người, ngày, giờ,
 * loại việc, ưu tiên. Lỗi của chính dòng (cả lỗi máy chủ trả về) hiện ngay dưới nó.
 */
export function AiPlanRowEditor({
  row,
  compact = false,
  readOnly,
  people,
  taskTypes,
  problems,
  onChange,
  onRemove,
  children,
}: AiPlanRowEditorProps) {
  const label = compact ? 'việc con' : 'việc'
  const typeOptions =
    row.task_type && !taskTypes.some((type) => type.id === row.task_type?.id)
      ? [...taskTypes, row.task_type]
      : taskTypes
  const byId = new Map(people.map((person) => [person.employee_id, person]))

  return (
    <div
      role="group"
      aria-label={`${compact ? 'Việc con' : 'Việc'}: ${row.title || 'chưa đặt tên'}`}
      className={cn(
        'space-y-2 rounded-lg border bg-card p-3',
        compact && 'bg-muted/30',
        problems.length > 0 && 'border-destructive/60',
      )}
    >
      <div className="flex items-start gap-2">
        <Input
          value={row.title}
          readOnly={readOnly}
          aria-label={`Tên ${label}`}
          placeholder={`Tên ${label}`}
          maxLength={500}
          className={cn('h-9 flex-1', !compact && 'font-medium')}
          onChange={(event) => onChange({ title: event.target.value })}
        />
        {!readOnly && (
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            title={`Bỏ ${label} này`}
            aria-label={`Bỏ ${label} ${row.title || 'chưa đặt tên'}`}
            onClick={onRemove}
          >
            <Trash2 className="size-4 text-muted-foreground" />
          </Button>
        )}
      </div>

      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-[minmax(0,2fr)_repeat(4,minmax(0,1fr))]">
        <div aria-label={`Người làm ${label}`} role="group">
          <MultiPicker
            value={row.assignees.map((person) => person.employee_id)}
            onChange={(ids) =>
              onChange({
                assignees: ids.map((id) => {
                  const person = byId.get(id)
                  return { employee_id: id, code: person?.code ?? '', name: person?.name ?? `#${id}` }
                }),
              })
            }
            options={people.map((person) => ({
              id: person.employee_id,
              label: person.active ? person.name : `${person.name} (không còn trong danh bạ)`,
              hint: person.code,
            }))}
            placeholder="Chưa giao ai"
            searchPlaceholder="Tìm theo tên hoặc mã…"
            emptyMessage="Không tìm thấy nhân sự nào."
            disabled={readOnly}
            chipsInTrigger
          />
        </div>
        <DatePicker
          value={row.start_date}
          onChange={(value) => onChange({ start_date: value })}
          placeholder="Bắt đầu"
          size="sm"
          clearable
          disabled={readOnly}
        />
        <DatePicker
          value={row.due_date}
          onChange={(value) => onChange({ due_date: value })}
          placeholder="Hạn"
          size="sm"
          clearable
          disabled={readOnly}
        />
        <Select
          value={row.priority || 'Thường'}
          onValueChange={(value) => onChange({ priority: value })}
          disabled={readOnly}
        >
          <SelectTrigger className="h-8 text-xs" aria-label={`Ưu tiên ${label}`}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {AI_PLAN_PRIORITIES.map((priority) => (
              <SelectItem key={priority} value={priority}>
                {priority}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Input
          inputMode="decimal"
          defaultValue={row.estimate_hours === null ? '' : String(row.estimate_hours)}
          readOnly={readOnly}
          aria-label={`Giờ ước lượng ${label}`}
          placeholder="Giờ ước lượng"
          className="h-8 text-xs"
          onChange={(event) => onChange({ estimate_hours: parseHours(event.target.value) })}
        />
      </div>

      {!compact && (
        <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
          <Select
            value={row.task_type ? String(row.task_type.id) : NO_TYPE}
            onValueChange={(value) =>
              onChange({
                task_type:
                  value === NO_TYPE ? null : (typeOptions.find((type) => String(type.id) === value) ?? null),
              })
            }
            disabled={readOnly}
          >
            <SelectTrigger className="h-8 text-xs" aria-label="Loại việc">
              <SelectValue placeholder="Loại việc" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={NO_TYPE}>Chưa chọn loại việc</SelectItem>
              {typeOptions.map((type) => (
                <SelectItem key={type.id} value={String(type.id)}>
                  {type.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Textarea
            value={row.description}
            readOnly={readOnly}
            aria-label="Mô tả việc"
            placeholder="Mô tả"
            rows={1}
            maxLength={2000}
            className="min-h-8 text-xs"
            onChange={(event) => onChange({ description: event.target.value })}
          />
        </div>
      )}

      {!compact && row.assignee_reason && (
        //  Lý do AI chọn người: người duyệt cần đọc để quyết có đổi người hay không.
        <p className="flex items-start gap-1.5 text-xs text-muted-foreground">
          <Sparkles className="mt-0.5 size-3.5 shrink-0" />
          <span>
            <span className="font-medium">Vì sao chọn người này:</span> {row.assignee_reason}
          </span>
        </p>
      )}

      {!compact && row.criteria.length > 0 && (
        <ul className="list-disc pl-5 text-xs text-muted-foreground" aria-label="Tiêu chí xong việc">
          {row.criteria.map((criterion, index) => (
            <li key={index}>{criterion}</li>
          ))}
        </ul>
      )}

      {problems.length > 0 && (
        <ul className="space-y-0.5 text-xs text-destructive" role="alert">
          {problems.map((message, index) => (
            <li key={index}>{message}</li>
          ))}
        </ul>
      )}

      {children}
    </div>
  )
}
