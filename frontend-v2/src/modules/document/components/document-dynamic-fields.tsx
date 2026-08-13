import type { UseFormReturn } from 'react-hook-form'

import { Checkbox } from '@/shared/ui/checkbox'
import { FormCard } from '@/shared/ui/form-card'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import type { DocumentRecordFormValues } from '../schemas/document-record-schema'
import type { DynamicField } from '../types/dynamic-field'

interface DocumentDynamicFieldsProps {
  fields: DynamicField[]
  form: UseFormReturn<DocumentRecordFormValues>
}

/**
 * Các ô nhập do người quản trị khai trong danh mục Trường thông tin động, đổi
 * theo LOẠI văn bản đang chọn.
 *
 * Giá trị lưu hết vào `field_values` dưới dạng CHUỖI, tra theo `code`: bảng dữ
 * liệu không thể có cột cho những trường sinh ra sau khi hệ đã chạy.
 */
export function DocumentDynamicFields({ fields, form }: DocumentDynamicFieldsProps) {
  if (fields.length === 0) return null

  const values = form.watch('field_values')
  const setValue = (code: string, value: string) =>
    form.setValue('field_values', { ...values, [code]: value }, { shouldDirty: true })

  return (
    // Không đặt tên "Thông tin bổ sung": khối ngay trên đã mang tên đó, hai thẻ
    // trùng tên thì không biết ô nào thuộc đâu.
    <FormCard
      title="Trường thông tin theo loại văn bản"
      contentClassName="grid items-start gap-x-4 gap-y-3 sm:grid-cols-2"
    >
      {fields.map((field) => {
        const value = values?.[field.code] ?? ''
        const inputId = `dynamic-${field.code}`

        return (
          <div key={field.id} className="space-y-1.5">
            <Label htmlFor={inputId}>
              {field.label}
              {field.is_required && <span className="text-destructive"> *</span>}
            </Label>

            {field.field_type === 'textarea' && (
              <Textarea
                id={inputId}
                rows={3}
                value={value}
                onChange={(event) => setValue(field.code, event.target.value)}
              />
            )}

            {field.field_type === 'select' && (
              <Select value={value} onValueChange={(next) => setValue(field.code, next)}>
                <SelectTrigger id={inputId} className="w-full">
                  <SelectValue placeholder="Chọn…" />
                </SelectTrigger>
                <SelectContent>
                  {field.options.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}

            {field.field_type === 'checkbox' && (
              <div className="flex h-9 items-center">
                <Checkbox
                  id={inputId}
                  checked={value === 'true'}
                  onCheckedChange={(checked) =>
                    setValue(field.code, checked === true ? 'true' : 'false')
                  }
                />
              </div>
            )}

            {['text', 'number', 'date'].includes(field.field_type) && (
              <Input
                id={inputId}
                type={field.field_type === 'text' ? 'text' : field.field_type}
                value={value}
                onChange={(event) => setValue(field.code, event.target.value)}
              />
            )}

            {field.help_text && (
              <p className="text-xs text-muted-foreground">{field.help_text}</p>
            )}
          </div>
        )
      })}
    </FormCard>
  )
}
