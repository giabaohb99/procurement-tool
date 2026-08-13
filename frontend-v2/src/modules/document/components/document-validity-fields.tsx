import type { UseFormReturn } from 'react-hook-form'

import { DatePicker } from '@/shared/ui/date-picker'
import { FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/shared/ui/form'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { useSecurityLevelOptions } from '../hooks/use-document-catalogs'
import type { DocumentRecordFormValues } from '../schemas/document-record-schema'
import { STATUS_LABELS } from '../types/document-record'

/** Giá trị của ô select khi người dùng chọn "không chọn gì". */
const NONE = 'none'

interface DocumentValidityFieldsProps {
  form: UseFormReturn<DocumentRecordFormValues>
}

/**
 * HIỆU LỰC PHÁP LÝ của văn bản + mức khẩn theo thang lưu trữ.
 *
 * Chỉ hiện ở trang chi tiết: lúc mới vào sổ chưa ai biết văn bản sẽ được thay
 * thế hay thu hồi khi nào, bắt khai ngay là khai bừa. Vẫn nằm trong bản ghi để
 * màn danh sách tính được "Hết hiệu lực" (xem `helpers/document-status.ts`).
 */
export function DocumentValidityFields({ form }: DocumentValidityFieldsProps) {
  const urgentLevels = useSecurityLevelOptions('urgent')

  return (
    <>
      <FormField
        control={form.control}
        name="urgent_level_id"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Mức độ khẩn</FormLabel>
            <Select
              value={field.value ? String(field.value) : NONE}
              onValueChange={(value) => field.onChange(value === NONE ? null : Number(value))}
            >
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value={NONE}>Không đặt</SelectItem>
                {urgentLevels.map((level) => (
                  <SelectItem key={level.id} value={String(level.id)}>
                    {level.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="status"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Hiệu lực</FormLabel>
            <Select value={field.value} onValueChange={field.onChange}>
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {Object.entries(STATUS_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="effective_from"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Hiệu lực từ</FormLabel>
            <FormControl>
              <DatePicker value={field.value} onChange={field.onChange} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="effective_to"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Hiệu lực đến</FormLabel>
            <FormControl>
              <DatePicker value={field.value} onChange={field.onChange} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </>
  )
}
