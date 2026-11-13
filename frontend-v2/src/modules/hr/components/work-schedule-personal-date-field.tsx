import { useController, type Control } from 'react-hook-form'

import type { CrudRecord } from '@/shared/crud'
import { DatePicker } from '@/shared/ui/date-picker'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { RequiredMark } from '@/shared/ui/required-mark'
import { formatDate } from '@/shared/utils/format-date'

interface WorkSchedulePersonalDateFieldProps {
  control: Control<CrudRecord>
  /** Tên ô trong form (`effective_from` / `effective_to`). */
  name: string
  label: string
  required?: boolean
  /** Ô bị khóa (dòng đã bắt đầu / đã thay lịch trước đó): hiện chữ chỉ xem, không phải ô chọn bị tắt. */
  readOnly?: boolean
  /** Luật ngày riêng của đường Trưởng phòng; trả câu lỗi hoặc `true`. Không gọi khi ô khóa. */
  validate?: (value: string) => true | string
  /** Các câu dưới ô, theo thứ tự. */
  hints?: (string | undefined)[]
  /** Chữ hiện khi ô chỉ xem mà trống (vd "Không thời hạn"). */
  emptyLabel?: string
}

/**
 * Ô ngày của hộp gán lịch RIÊNG cho Trưởng phòng (duoc-CR-757 lượt 2): chặn ngày sai luật ngay trên biểu mẫu, cùng
 * câu với backend (422). Ô chọn ngày chung chưa có mốc tối thiểu nên chặn bằng luật kiểm của biểu mẫu + câu nhắc, không
 * làm mờ ngày trên lịch.
 */
export function WorkSchedulePersonalDateField({
  control,
  name,
  label,
  required = false,
  readOnly = false,
  validate,
  hints = [],
  emptyLabel = '',
}: WorkSchedulePersonalDateFieldProps) {
  const { field, fieldState } = useController({
    control,
    name,
    rules: {
      required: required && !readOnly ? `${label} là bắt buộc` : false,
      validate: (value) => readOnly || !validate || validate(String(value ?? '')),
    },
  })
  const value = String(field.value ?? '')

  return (
    <div className="space-y-1.5">
      <Label htmlFor={readOnly ? undefined : name}>
        {label}
        {required && <RequiredMark />}
      </Label>
      {readOnly ? (
        <ReadOnlyValue>{value ? formatDate(value) : emptyLabel}</ReadOnlyValue>
      ) : (
        <DatePicker id={name} value={value} onChange={field.onChange} clearable={!required} />
      )}
      {fieldState.error?.message && (
        <p role="alert" className="text-xs text-destructive">
          {fieldState.error.message}
        </p>
      )}
      {hints.filter(Boolean).map((hint) => (
        <p key={hint} className="text-xs text-muted-foreground">
          {hint}
        </p>
      ))}
    </div>
  )
}
