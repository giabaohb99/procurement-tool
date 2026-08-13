import type { UseFormReturn } from 'react-hook-form'

import { DatePicker } from '@/shared/ui/date-picker'
import {
  FormControl,
  FormDescription,
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
import { useDepartmentNames, useEmployeeNames } from '../hooks/use-document-people'
import { useActiveDocumentTypes } from '../hooks/use-document-types'
import { useNextDocumentCode } from '../hooks/use-documents'
import type { DocumentRecordFormValues } from '../schemas/document-record-schema'
import { BOOK_LABELS } from '../types/document-record'
import { DocumentPartnerFields } from './document-partner-fields'
import { DocumentPriorityToggle } from './document-priority-toggle'
import { DocumentRecipientPicker } from './document-recipient-picker'
import { NameSelect } from './name-select'

/** Các trường thuộc bước "Thông tin chính" — kiểm khi bấm "Tiếp tục". */
export const MAIN_INFO_FIELDS = [
  'direction',
  'document_type_id',
  'title',
  'code',
  'issued_date',
  'approver',
  'required_due_date',
  'drafting_department',
] as const

interface DocumentMainInfoFieldsProps {
  form: UseFormReturn<DocumentRecordFormValues>
  /**
   * Đang sửa văn bản đã vào sổ: khóa ô số văn bản và mở thêm những ô chỉ dùng
   * lúc rà soát lại (nơi gửi theo danh mục, ngày đến).
   */
  isEditing: boolean
}

/** Dấu * đỏ sau nhãn của ô bắt buộc. */
function Required() {
  return <span className="text-destructive"> *</span>
}

/**
 * THÔNG TIN CHÍNH của văn bản: tên, số, ngày ban hành, ai duyệt, gửi cho ai.
 *
 * Dùng chung cho bước 1 của trang tạo mới và tab "Thông tin" của trang chi tiết
 * — hai chỗ đó phải hỏi y hệt nhau, tách ra là sớm muộn cũng lệch.
 */
export function DocumentMainInfoFields({ form, isEditing }: DocumentMainInfoFieldsProps) {
  const direction = form.watch('direction')
  const documentTypes = useActiveDocumentTypes()
  const employeeNames = useEmployeeNames()
  const departmentNames = useDepartmentNames()

  const suggestedCode = useNextDocumentCode(
    direction,
    form.watch('issued_date'),
    form.watch('document_type_id'),
  )

  return (
    // Lưới 2 cột, nhãn nằm trên ô nhập. Ô nào dài (tên văn bản, nơi nhận) thì
    // cho ăn hết bề ngang bằng `sm:col-span-2`.
    <div className="grid items-start gap-x-5 gap-y-3 sm:grid-cols-2">
      {/* Hỏi SỔ và LOẠI trước tên: hai ô này quyết định số hiệu gợi ý ở ô ngay
          dưới và bộ trường động ở bước 3 — chọn sau thì mấy ô kia đổi dưới tay
          người đang nhập. */}
      <FormField
        control={form.control}
        name="direction"
        render={({ field }) => (
          <FormItem>
            <FormLabel>
              Vào sổ
              <Required />
            </FormLabel>
            {/* Sổ nào thì cấp số theo sổ đó — đổi sổ sau khi đã vào sổ là mọi
                giấy tờ đã phát hành thành sai, nên lúc sửa thì khóa. */}
            <Select value={field.value} onValueChange={field.onChange} disabled={isEditing}>
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Chọn sổ văn bản" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {Object.entries(BOOK_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormDescription>
              {isEditing
                ? 'Không đổi được: văn bản đã vào sổ này.'
                : 'Văn bản đến / đi / nội bộ — mỗi sổ đánh số riêng theo năm.'}
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="document_type_id"
        render={({ field }) => (
          <FormItem>
            <FormLabel>
              Loại văn bản
              <Required />
            </FormLabel>
            <Select
              value={field.value ? String(field.value) : ''}
              onValueChange={(value) => field.onChange(Number(value))}
            >
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Chọn loại văn bản" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {documentTypes.map((type) => (
                  <SelectItem key={type.id} value={String(type.id)}>
                    {type.name}
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
        name="title"
        render={({ field }) => (
          <FormItem className="sm:col-span-2">
            <FormLabel>
              Tên văn bản
              <Required />
            </FormLabel>
            <FormControl>
              <Input placeholder="Nhập tên văn bản" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="code"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Số văn bản</FormLabel>
            <FormControl>
              <Input placeholder={suggestedCode} disabled={isEditing} {...field} />
            </FormControl>
            <FormDescription>
              {isEditing
                ? 'Không đổi được: văn bản đã vào sổ với số này.'
                : `Để trống thì hệ cấp số ${suggestedCode}.`}
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormItem>
        <FormLabel>Mức độ quan trọng, khẩn cấp</FormLabel>
        <DocumentPriorityToggle
          isImportant={form.watch('is_important')}
          isUrgent={form.watch('is_urgent')}
          onChange={(next) => {
            form.setValue('is_important', next.is_important)
            form.setValue('is_urgent', next.is_urgent)
          }}
        />
      </FormItem>

      <FormField
        control={form.control}
        name="issued_date"
        render={({ field }) => (
          <FormItem>
            <FormLabel>
              Ngày ban hành
              <Required />
            </FormLabel>
            <FormControl>
              {/* Bắt buộc nên không cho xóa — xem `docs/ui/date.md`. */}
              <DatePicker value={field.value} onChange={field.onChange} clearable={false} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="approver"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Người phê duyệt (Trưởng phòng)</FormLabel>
            <FormControl>
              <NameSelect
                value={field.value}
                onChange={field.onChange}
                options={employeeNames}
                placeholder="-- Mặc định --"
                emptyLabel="-- Mặc định --"
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="required_due_date"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Thời hạn văn bản yêu cầu</FormLabel>
            <FormControl>
              <DatePicker value={field.value} onChange={field.onChange} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="drafting_department"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Đơn vị soạn thảo</FormLabel>
            <FormControl>
              <NameSelect
                value={field.value}
                onChange={field.onChange}
                options={departmentNames}
                placeholder="Chọn đơn vị soạn thảo"
                emptyLabel="-- Chưa chọn --"
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="recipients"
        render={({ field }) => (
          <FormItem className="sm:col-span-2">
            <FormLabel>Nơi nhận</FormLabel>
            <FormControl>
              <DocumentRecipientPicker value={field.value} onChange={field.onChange} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      {isEditing && <DocumentPartnerFields form={form} direction={direction} />}
    </div>
  )
}
