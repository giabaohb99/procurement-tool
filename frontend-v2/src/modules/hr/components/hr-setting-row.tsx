import type { ReactNode } from 'react'

import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { MultiPicker } from '@/shared/ui/multi-picker'
import { Switch } from '@/shared/ui/switch'
import { cn } from '@/shared/utils/cn'
import type { HrSettingField, HrSettingValue } from '../types/hr-setting'

interface HrSettingRowProps {
  field: HrSettingField
  value: HrSettingValue
  onChange: (value: HrSettingValue) => void
  /** Không có quyền sửa, hoặc công tắc mà ô này phụ thuộc đang TẮT. */
  disabled: boolean
  /** Làm mờ (công tắc cha TẮT) — vẫn đọc được giá trị, chỉ báo «chưa có tác dụng». */
  muted?: boolean
  /** Danh sách vai trò cho ô `roles`; `null` = không có `role.read` → hiện mã trơn. */
  roleOptions: { id: string; label: string; hint: string }[] | null
}

/**
 * Một dòng cài đặt, vẽ theo `type` backend khai: công tắc (`bool`) nằm bên phải nhãn; ô nhập (`int`, `str`,
 * `code_prefix`, `int_list`) và ô chọn vai trò (`roles`) nằm dưới nhãn. Lời giải thích lấy nguyên từ backend.
 */
export function HrSettingRow({ field, value, onChange, disabled, muted, roleOptions }: HrSettingRowProps) {
  const id = `hr-setting-${field.key}`
  const hint = field.hint && <p className="max-w-3xl text-sm text-muted-foreground">{field.hint}</p>

  if (field.type === 'bool') {
    return (
      <Row muted={muted}>
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 space-y-1">
            <Label htmlFor={id} className="text-sm font-medium">
              {field.label}
            </Label>
            {hint}
          </div>
          <Switch id={id} checked={value === true} onCheckedChange={onChange} disabled={disabled} />
        </div>
      </Row>
    )
  }

  let control: ReactNode
  if (field.type === 'roles') {
    const codes = Array.isArray(value) ? value : []
    control = roleOptions ? (
      <MultiPicker<string>
        value={codes}
        onChange={onChange}
        options={roleOptions}
        placeholder="Chọn vai trò được miễn"
        searchPlaceholder="Tìm vai trò…"
        emptyMessage="Không có vai trò nào."
        disabled={disabled}
      />
    ) : (
      <p className="text-sm">{codes.join(', ') || '(chưa khai vai trò nào)'}</p>
    )
  } else {
    control = (
      <Input
        id={id}
        value={typeof value === 'string' ? value : ''}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
        inputMode={field.type === 'int' ? 'numeric' : undefined}
        className={cn('max-w-xs', field.type === 'code_prefix' && 'uppercase')}
        placeholder={field.type === 'int' && field.min !== undefined ? `${field.min}–${field.max}` : undefined}
      />
    )
  }

  return (
    <Row muted={muted}>
      <div className="space-y-1.5">
        <Label htmlFor={id} className="text-sm font-medium">
          {field.label}
        </Label>
        {control}
        {hint}
      </div>
    </Row>
  )
}

function Row({ muted, children }: { muted?: boolean; children: ReactNode }) {
  return <div className={cn('p-4', muted && 'opacity-60')}>{children}</div>
}
