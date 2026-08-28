import { X } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import type { WorkLabelField, WorkMember, WorkTaskLabelValue } from '../types/work'
import { WORK_FIELD_TYPE } from '../types/work'
import { chipClass } from '../utils/work-colors'

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
    case WORK_FIELD_TYPE.MULTI:
      return (
        <MultiOptionInput
          field={field}
          chosen={values.map((v) => v.option_id).filter((id): id is number => id !== null)}
          disabled={disabled}
          onChange={onChange}
        />
      )

    case WORK_FIELD_TYPE.PERSON:
      //  Chọn trong THÀNH VIÊN của dự án, không phải toàn bộ danh bạ: gán một
      //  người ngoài dự án thì họ không mở nổi task để biết mình bị gán.
      return (
        <Select
          value={String(first?.value_employee_id ?? 'none')}
          disabled={disabled}
          onValueChange={(v) => onChange(v === 'none' ? null : Number(v))}
        >
          <SelectTrigger size="sm" className="w-44">
            <SelectValue placeholder="Chưa chọn" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">Chưa chọn</SelectItem>
            {members.map((m) => (
              <SelectItem key={m.employee_id} value={String(m.employee_id)}>
                {m.employee_name || `#${m.employee_id}`}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )

    case WORK_FIELD_TYPE.NUMBER:
      return (
        <Input
          type="number"
          className="w-44"
          disabled={disabled}
          defaultValue={first?.value_number ?? ''}
          placeholder="Nhập số"
          //  Ghi lúc RỜI ô, không phải mỗi phím: gõ "12.5" mà bắn theo từng
          //  ký tự thì máy chủ nhận cả "12." và trả lỗi giữa chừng.
          onBlur={(e) => onChange(e.target.value.trim() === '' ? null : e.target.value)}
        />
      )

    case WORK_FIELD_TYPE.DATE:
      return (
        <DatePicker
          size="sm"
          clearable
          value={first?.value_date ?? ''}
          disabled={disabled}
          onChange={(value) => onChange(value || null)}
        />
      )

    case WORK_FIELD_TYPE.TEXT:
      return (
        <Input
          className="w-full"
          disabled={disabled}
          defaultValue={first?.value_text ?? ''}
          placeholder="Nhập nội dung"
          maxLength={500}
          onBlur={(e) => onChange(e.target.value.trim() === '' ? null : e.target.value)}
        />
      )

    default:
      return (
        <Select
          value={String(first?.option_id ?? 'none')}
          disabled={disabled}
          onValueChange={(v) => onChange(v === 'none' ? null : Number(v))}
        >
          <SelectTrigger size="sm" className="w-44">
            <SelectValue placeholder="Chưa chọn" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">Chưa chọn</SelectItem>
            {field.options.map((o) => (
              <SelectItem key={o.id} value={String(o.id)}>
                {o.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )
  }
}

/**
 * Chọn NHIỀU giá trị: bấm chip để bật/tắt.
 *
 * Không dùng `Select` nhiều lựa chọn vì shadcn/Radix không có sẵn kiểu đó, mà
 * dựng thêm một popover chỉ để tick vài giá trị thì nặng hơn hàng chip — chip
 * lại hiện đúng màu như trên thẻ nên nhìn là biết đang chọn gì.
 */
function MultiOptionInput({
  field,
  chosen,
  disabled,
  onChange,
}: {
  field: WorkLabelField
  chosen: number[]
  disabled?: boolean
  onChange: (value: number[] | null) => void
}) {
  function toggle(optionId: number) {
    const next = chosen.includes(optionId)
      ? chosen.filter((id) => id !== optionId)
      : [...chosen, optionId]
    //  Bỏ hết thì gửi `null` chứ không phải mảng rỗng — cùng một nghĩa "bỏ
    //  chọn" với năm kiểu kia, khỏi để máy chủ đoán.
    onChange(next.length === 0 ? null : next)
  }

  if (field.options.length === 0) {
    return <span className="text-sm text-muted-foreground">Trường chưa khai giá trị</span>
  }

  return (
    <div className="flex flex-wrap items-center gap-1">
      {field.options.map((o) => {
        const on = chosen.includes(o.id)
        return (
          <button
            key={o.id}
            type="button"
            disabled={disabled}
            onClick={() => toggle(o.id)}
            className={cn(
              'rounded px-1.5 py-0.5 text-[11px] font-medium transition-opacity',
              chipClass(o.color),
              //  Giá trị KHÔNG chọn vẫn hiện, chỉ mờ đi: giấu hẳn thì người
              //  dùng không biết trường này còn chọn được gì nữa.
              !on && 'opacity-35',
              disabled ? 'cursor-default' : 'cursor-pointer hover:opacity-100',
            )}
          >
            {o.name}
          </button>
        )
      })}
      {chosen.length > 0 && !disabled && (
        <Button
          variant="ghost"
          size="icon"
          className="size-6"
          title="Bỏ chọn hết"
          onClick={() => onChange(null)}
        >
          <X className="size-3.5" />
        </Button>
      )}
    </div>
  )
}
