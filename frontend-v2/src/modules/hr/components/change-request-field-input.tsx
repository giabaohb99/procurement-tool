import { useId } from 'react'

import { EMPLOYEE_FIELD_DEFS, type EmployeeFieldKey } from '../config/employee-profile-fields'
import type { ChangeRequestValue } from '../types/employee-change-request'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'

interface ChangeRequestFieldInputProps {
  field: EmployeeFieldKey
  value: ChangeRequestValue | undefined
  onChange: (value: ChangeRequestValue) => void
}

/**
 * Một ô nhập của hộp «Đề nghị sửa thông tin» (duoc-CR-676) — dựng theo KIỂU khai ở
 * `EMPLOYEE_FIELD_DEFS`, nên thêm ô mới chỉ cần khai ở đó.
 *
 * Nhãn nối đúng vào ô bằng `useId` (trình đọc màn hình đọc ra tên ô, bấm chữ nhảy vào ô).
 */
export function ChangeRequestFieldInput({ field, value, onChange }: ChangeRequestFieldInputProps) {
  const id = useId()
  const def = EMPLOYEE_FIELD_DEFS[field]

  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>{def.label}</Label>
      {def.kind === 'date' ? (
        <DatePicker
          id={id}
          value={typeof value === 'string' ? value : ''}
          onChange={(next) => onChange(next || null)}
        />
      ) : def.kind === 'code' ? (
        <Select value={String(value ?? 0)} onValueChange={(next) => onChange(Number(next))}>
          <SelectTrigger id={id} className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {('options' in def ? def.options : []).map((option) => (
              <SelectItem key={option.value} value={String(option.value)}>
                {/*  Mục `0` = chưa khai: nhãn bên bộ mã để rỗng, Radix cấm value rỗng nên vẫn
                     phải có mục, chỉ là gắn chữ cho nó. */}
                {option.value === 0 ? '— Chưa khai —' : option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      ) : def.kind === 'number' ? (
        <Input
          id={id}
          type="number"
          min={0}
          value={String(value ?? 0)}
          onChange={(event) => onChange(Math.max(0, Number(event.target.value) || 0))}
        />
      ) : (
        <Input
          id={id}
          type={'inputType' in def ? def.inputType : 'text'}
          maxLength={'maxLength' in def ? def.maxLength : undefined}
          value={value === null || value === undefined ? '' : String(value)}
          onChange={(event) => onChange(event.target.value)}
        />
      )}
    </div>
  )
}
