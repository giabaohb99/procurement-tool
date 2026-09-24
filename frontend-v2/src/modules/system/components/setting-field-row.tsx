import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Switch } from '@/shared/ui/switch'
import { cn } from '@/shared/utils/cn'

import type { SettingField } from '../types/setting'

import { SettingDocLink } from './setting-doc-link'

interface SettingFieldRowProps {
  field: SettingField
  disabled: boolean
  onChange: (key: string, value: unknown) => void
}

/**
 * Vẽ MỘT trường cấu hình theo `type` backend khai báo.
 *
 * Cố tình viết dạng tổng quát thay vì liệt kê từng ô: danh sách cấu hình nằm ở
 * `modules/setting/service.py`, thêm một dòng ở đó là màn này tự có ô mới. Kiểu
 * lạ (backend thêm `type` mới mà frontend chưa biết) thì rơi về ô chữ — thà sửa
 * được dưới dạng chuỗi còn hơn biến mất khỏi màn hình.
 */
export function SettingFieldRow({ field, disabled, onChange }: SettingFieldRowProps) {
  const inputId = `setting-${field.key}`

  if (field.type === 'bool') {
    const checked = field.value === true || field.value === 'true'
    return (
      <div className={cn('py-2', field.hint && 'sm:col-span-2')}>
        <div className="flex items-center gap-3">
          <Switch
            id={inputId}
            checked={checked}
            disabled={disabled}
            onCheckedChange={(next) => onChange(field.key, next)}
          />
          <Label htmlFor={inputId} className="cursor-pointer text-[13px] font-medium">
            {field.label}
          </Label>
          <span
            className={cn(
              'text-xs',
              checked ? 'font-medium text-emerald-600' : 'text-muted-foreground',
            )}
          >
            {checked ? 'Đang bật' : 'Đang tắt'}
          </span>
        </div>
        {field.hint && <Hint text={field.hint} />}
      </div>
    )
  }

  if (field.type === 'select') {
    //  Radix `Select` không nhận `value=""` (xem lời giải ở `shared/ui/select.tsx`),
    //  nên ô chưa đặt để `undefined` và hiện chữ gợi ý thay vì một dòng rỗng.
    const current = typeof field.value === 'string' && field.value ? field.value : undefined
    return (
      <div className={cn('flex flex-col gap-1.5 py-2', field.hint && 'sm:col-span-2')}>
        <FieldLabel field={field} inputId={inputId} />
        <Select value={current} disabled={disabled} onValueChange={(next) => onChange(field.key, next)}>
          <SelectTrigger id={inputId} className="w-full">
            <SelectValue placeholder="— Chưa chọn —" />
          </SelectTrigger>
          <SelectContent>
            {(field.options ?? []).map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {field.hint && <Hint text={field.hint} />}
      </div>
    )
  }

  const isNumber = field.type === 'int'
  return (
    <div className={cn('flex flex-col gap-1.5 py-2', field.hint && 'sm:col-span-2')}>
      <FieldLabel field={field} inputId={inputId} />
      <Input
        id={inputId}
        type={isNumber ? 'number' : 'text'}
        disabled={disabled}
        value={typeof field.value === 'string' || typeof field.value === 'number' ? field.value : ''}
        onChange={(event) =>
          onChange(
            field.key,
            // Ô số để trống phải gửi lên chuỗi rỗng chứ không phải `0` — `Number('')`
            // ra 0, lưu lại là tự dựng cổng SMTP thành 0.
            isNumber && event.target.value !== ''
              ? Number(event.target.value)
              : event.target.value,
          )
        }
      />
      {field.hint && <Hint text={field.hint} />}
    </div>
  )
}

/** Nhãn ô, kèm link ra chỗ lấy giá trị khi backend có khai `doc_url`. */
function FieldLabel({ field, inputId }: { field: SettingField; inputId: string }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <Label htmlFor={inputId} className="text-[13px]">
        {field.label}
      </Label>
      {field.doc_url && <SettingDocLink href={field.doc_url} />}
    </div>
  )
}

function Hint({ text }: { text: string }) {
  return <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{text}</p>
}
