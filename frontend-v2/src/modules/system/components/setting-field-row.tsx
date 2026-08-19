import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Switch } from '@/shared/ui/switch'
import { cn } from '@/shared/utils/cn'

import type { SettingField } from '../types/setting'

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

  const isNumber = field.type === 'int'
  return (
    <div className={cn('flex flex-col gap-1.5 py-2', field.hint && 'sm:col-span-2')}>
      <Label htmlFor={inputId} className="text-[13px]">
        {field.label}
      </Label>
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

function Hint({ text }: { text: string }) {
  return <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{text}</p>
}
