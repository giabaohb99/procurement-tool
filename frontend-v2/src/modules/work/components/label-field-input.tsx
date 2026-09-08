import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { cn } from '@/shared/utils/cn'
import type { WorkLabelField, WorkMember, WorkTaskLabelValue } from '../types/work'
import { WORK_FIELD_TYPE } from '../types/work'
import { personName } from '../utils/people'
import { LabelMultiCell } from './label-multi-cell'
import { TaskChipSelect } from './task-chip-select'

interface LabelFieldInputProps {
  field: WorkLabelField
  /** Mọi giá trị của TRƯỜNG NÀY trên task (kiểu chọn nhiều có thể có vài cái). */
  values: WorkTaskLabelValue[]
  disabled?: boolean
  /** Thành viên dự án — nguồn cho trường kiểu NGƯỜI. */
  members: WorkMember[]
  /** Giá trị mới, đa hình theo kiểu trường; `null` = bỏ chọn. */
  onChange: (value: unknown) => void
}

/**
 * Ô nhập của MỘT trường tùy biến, tự đổi hình theo `field_type` (B-13).
 *
 * Gom sáu kiểu vào một chỗ thay vì rải if/else khắp panel chi tiết: thêm kiểu
 * thứ bảy về sau chỉ phải sửa đúng tệp này, và thẻ với panel không lệch nhau.
 */
export function LabelFieldInput({
  field,
  values,
  disabled,
  members,
  onChange,
}: LabelFieldInputProps) {
  const first = values[0]

  switch (field.field_type) {
    case WORK_FIELD_TYPE.MULTI: {
      const chosen = values.map((v) => v.option_id).filter((id): id is number => id !== null)
      //  MỘT dáng duy nhất cho cả bảng lẫn panel: ô CHỌN NHIỀU có mũi tên.
      //  Panel từng bày thẳng MỌI giá trị của trường thành một dải chip bật/tắt
      //  — trường khai bốn năm giá trị là một mảng màu chiếm cả hàng, phải dò
      //  từng cái xem cái nào đang mờ (= chưa chọn), mà nó lại chẳng giống ô
      //  chọn nào khác trong panel. Khách chốt 03/09/2026: mở ô chọn.
      return (
        <LabelMultiCell field={field} chosen={chosen} disabled={disabled} onChange={onChange} />
      )
    }

    case WORK_FIELD_TYPE.PERSON:
      //  Chọn trong THÀNH VIÊN của dự án, không phải toàn bộ danh bạ: gán một
      //  người ngoài dự án thì họ không mở nổi task để biết mình bị gán.
      return (
        <TaskChipSelect
          ariaLabel={field.name}
          placeholder="Chưa chọn"
          value={String(first?.value_employee_id ?? NONE)}
          options={[
            { value: NONE, label: 'Chưa chọn' },
            ...members.map((m) => ({
              value: String(m.employee_id),
              label: personName(m.employee_name, m.employee_id),
            })),
          ]}
          disabled={disabled}
          onChange={(v) => onChange(v === NONE ? null : Number(v))}
        />
      )

    case WORK_FIELD_TYPE.NUMBER:
      return (
        <PlainTextInput
          type="number"
          className="w-44"
          disabled={disabled}
          value={first?.value_number ?? ''}
          placeholder="Nhập số"
          //  Ghi lúc RỜI ô, không phải mỗi phím: gõ "12.5" mà bắn theo từng
          //  ký tự thì máy chủ nhận cả "12." và trả lỗi giữa chừng.
          onSave={(value) => onChange(value === '' ? null : value)}
        />
      )

    case WORK_FIELD_TYPE.DATE:
      return (
        <DatePicker
          size="sm"
          clearable
          className="w-auto"
          placeholder="Chưa đặt"
          value={first?.value_date ?? ''}
          disabled={disabled}
          onChange={(value) => onChange(value || null)}
        />
      )

    case WORK_FIELD_TYPE.TEXT:
      return (
        <PlainTextInput
          className="w-full"
          disabled={disabled}
          value={first?.value_text ?? ''}
          placeholder="Nhập nội dung"
          maxLength={500}
          onSave={(value) => onChange(value === '' ? null : value)}
        />
      )

    default:
      return (
        <TaskChipSelect
          ariaLabel={field.name}
          placeholder="Chưa chọn"
          value={String(first?.option_id ?? NONE)}
          options={[
            { value: NONE, label: 'Chưa chọn' },
            ...field.options.map((o) => ({
              value: String(o.id),
              label: o.name,
              color: o.color,
            })),
          ]}
          disabled={disabled}
          onChange={(v) => onChange(v === NONE ? null : Number(v))}
        />
      )
  }
}

/** Radix cấm `SelectItem value=""`, nên "chưa chọn" phải mang một mã riêng. */
const NONE = 'none'

/**
 * Ô nhập trông như CHỮ cho tới khi rê chuột vào — cùng lối với tiêu đề và mô tả
 * của panel, để hàng thuộc tính không bị viền hộp cắt vụn.
 *
 * Chỉ xem thì trả về `ReadOnlyValue` chứ KHÔNG phải `<Input disabled>`: ô mờ
 * không cho bôi đen/copy (luật giao diện của dự án).
 */
function PlainTextInput({
  value,
  onSave,
  disabled,
  className,
  ...props
}: {
  value: string
  onSave: (value: string) => void
  disabled?: boolean
  className?: string
} & Omit<React.ComponentProps<typeof Input>, 'value' | 'onBlur' | 'disabled'>) {
  if (disabled) return <ReadOnlyValue>{value}</ReadOnlyValue>

  return (
    <Input
      defaultValue={value}
      onBlur={(e) => onSave(e.target.value.trim())}
      className={cn(
        //  `dark:bg-transparent`: `Input` gốc có `dark:bg-input/30`, để nguyên
        //  thì nền tối lại hiện hộp xám đúng chỗ vừa bỏ viền.
        'h-7 border-0 bg-transparent px-1.5 shadow-none dark:bg-transparent',
        'hover:bg-accent/60 focus-visible:bg-background dark:focus-visible:bg-input/30',
        className,
      )}
      {...props}
    />
  )
}
