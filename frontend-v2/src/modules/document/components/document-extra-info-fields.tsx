import type { UseFormReturn } from 'react-hook-form'

import { DatePicker } from '@/shared/ui/date-picker'
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/shared/ui/form'
import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import { useSecurityLevelOptions } from '../hooks/use-document-catalogs'
import type { DocumentRecordFormValues } from '../schemas/document-record-schema'
import { DOCUMENT_FORMAT_LABELS } from '../types/document-record'
import { DocumentValidityFields } from './document-validity-fields'

/** Giá trị của ô select khi người dùng chọn "không chọn gì". */
const NONE = 'none'

interface DocumentExtraInfoFieldsProps {
  form: UseFormReturn<DocumentRecordFormValues>
  /** Đang sửa: mở thêm khối hiệu lực (xem `DocumentValidityFields`). */
  isEditing: boolean
}

/**
 * THÔNG TIN BỔ SUNG: hình thức bản lưu, mức mật, người ký, ngày đi, chỗ cất.
 *
 * Đều là thứ có thể bỏ trống lúc tạo rồi bổ sung sau, nên xếp sau cùng để người
 * nhập vào sổ được văn bản chỉ với vài ô bắt buộc ở bước đầu.
 */
export function DocumentExtraInfoFields({ form, isEditing }: DocumentExtraInfoFieldsProps) {
  const confidentialLevels = useSecurityLevelOptions('confidential')

  return (
    <div className="grid items-start gap-x-5 gap-y-3 sm:grid-cols-2">
      <FormField
        control={form.control}
        name="doc_format"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Hình thức văn bản</FormLabel>
            <Select value={field.value} onValueChange={field.onChange}>
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Chọn hình thức" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {Object.entries(DOCUMENT_FORMAT_LABELS).map(([value, label]) => (
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
        name="confidential_level_id"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Mức độ mật</FormLabel>
            <Select
              value={field.value ? String(field.value) : NONE}
              onValueChange={(value) => field.onChange(value === NONE ? null : Number(value))}
            >
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Chọn mức độ mật" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value={NONE}>Không đặt</SelectItem>
                {confidentialLevels.map((level) => (
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
        name="signer"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Người ký</FormLabel>
            <FormControl>
              <Input placeholder="Nhập người ký" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="sent_date"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Ngày đi</FormLabel>
            <FormControl>
              <DatePicker value={field.value} onChange={field.onChange} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="storage_location"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Vị trí lưu trữ</FormLabel>
            <FormControl>
              <Input placeholder="Nhập vị trí lưu trữ" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      {isEditing && <DocumentValidityFields form={form} />}

      <FormField
        control={form.control}
        name="summary"
        render={({ field }) => (
          <FormItem className="sm:col-span-2">
            <FormLabel>Trích yếu nội dung</FormLabel>
            <FormControl>
              <Textarea rows={6} placeholder="Tóm tắt nội dung văn bản…" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </div>
  )
}
