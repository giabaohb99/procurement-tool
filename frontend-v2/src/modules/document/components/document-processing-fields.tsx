import type { UseFormReturn } from 'react-hook-form'

import { DatePicker } from '@/shared/ui/date-picker'
import { FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/shared/ui/form'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { RadioGroup, RadioGroupItem } from '@/shared/ui/radio-group'
import { Textarea } from '@/shared/ui/textarea'
import { useEmployeeNames } from '../hooks/use-document-people'
import type { DocumentRecordFormValues } from '../schemas/document-record-schema'
import {
  NEW_DOCUMENT_PROCESSING_STATUSES,
  PROCESSING_STATUS_LABELS,
  type ProcessingStatus,
} from '../types/document-record'
import { NameSelect } from './name-select'

/** Các trường thuộc bước "Tình trạng xử lý". */
export const PROCESSING_FIELDS = [
  'processing_status',
  'due_date',
  'related_person',
  'handler',
  'report_receiver',
  'result',
] as const

interface DocumentProcessingFieldsProps {
  form: UseFormReturn<DocumentRecordFormValues>
  /** Đang sửa: mở thêm mức "Tạm dừng" và ô ghi chú xử lý. */
  isEditing: boolean
}

/**
 * TÌNH TRẠNG XỬ LÝ: văn bản đang nằm ở khâu nào, ai cầm, hạn bao giờ.
 *
 * Tách hẳn khỏi ô "Hiệu lực": hiệu lực nói về giá trị pháp lý của nội dung, còn
 * khối này nói về công việc — một quyết định còn hiệu lực vẫn có thể đang treo
 * ở khâu phát hành. Nhập chung một ô thì mất luôn một trong hai thông tin.
 */
export function DocumentProcessingFields({ form, isEditing }: DocumentProcessingFieldsProps) {
  const employeeNames = useEmployeeNames()

  const statuses: readonly ProcessingStatus[] = isEditing
    ? (Object.keys(PROCESSING_STATUS_LABELS) as ProcessingStatus[])
    : NEW_DOCUMENT_PROCESSING_STATUSES

  return (
    <div className="grid items-start gap-x-5 gap-y-3 sm:grid-cols-2">
      <FormField
        control={form.control}
        name="processing_status"
        render={({ field }) => (
          <FormItem className="sm:col-span-2">
            <FormLabel>
              Tình trạng
              <span className="text-destructive"> *</span>
            </FormLabel>
            <FormControl>
              {/* Bày sẵn thành hàng thay vì nhét vào select: người dùng thấy
                  ngay có những mức nào và bấm một nhát là xong. */}
              <RadioGroup value={field.value} onValueChange={field.onChange}>
                {statuses.map((value) => (
                  <div key={value} className="flex items-center gap-2">
                    <RadioGroupItem value={value} id={`processing-${value}`} />
                    <Label htmlFor={`processing-${value}`} className="font-normal">
                      {PROCESSING_STATUS_LABELS[value]}
                    </Label>
                  </div>
                ))}
              </RadioGroup>
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="due_date"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Hạn xử lý</FormLabel>
            <FormControl>
              <DatePicker value={field.value} onChange={field.onChange} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="related_person"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Người liên quan</FormLabel>
            <FormControl>
              <NameSelect
                value={field.value}
                onChange={field.onChange}
                options={employeeNames}
                placeholder="Chọn người liên quan"
                emptyLabel="-- Chưa chọn --"
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="handler"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Người xử lý</FormLabel>
            <FormControl>
              <NameSelect
                value={field.value}
                onChange={field.onChange}
                options={employeeNames}
                placeholder="Chọn người xử lý"
                emptyLabel="-- Chưa giao --"
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="report_receiver"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Người nhận báo cáo văn bản</FormLabel>
            <FormControl>
              <NameSelect
                value={field.value}
                onChange={field.onChange}
                options={employeeNames}
                placeholder="Chọn người nhận báo cáo văn bản"
                emptyLabel="-- Chưa chọn --"
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="result"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Kết quả xử lý</FormLabel>
            <FormControl>
              <Input placeholder="Nhập kết quả xử lý" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      {/* Chỉ hiện lúc sửa: lúc mới lập chưa có gì để ghi chú. */}
      {isEditing && (
        <FormField
          control={form.control}
          name="processing_note"
          render={({ field }) => (
            <FormItem className="sm:col-span-2">
              <FormLabel>Ghi chú xử lý</FormLabel>
              <FormControl>
                <Textarea
                  rows={3}
                  placeholder="Đã chuyển cho phòng nào, còn vướng gì…"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      )}
    </div>
  )
}
