import type { UseFormReturn } from 'react-hook-form'

import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/shared/ui/form'
import { Input } from '@/shared/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { useDocumentBooks } from '../hooks/use-document-books'
import { useActiveDocumentTemplates } from '../hooks/use-document-templates'
import { useActiveDocumentTypes } from '../hooks/use-document-types'
import { useNumberPreview } from '../hooks/use-documents'
import type { DocumentRecordFormValues } from '../schemas/document-record-schema'
import { DocumentNumberPreview } from './document-number-preview'
import { DocumentSuggestionList } from './document-suggestion-list'

/** Trường của bước "Thông tin chính" — kiểm khi bấm "Tiếp tục" ở trang tạo mới. */
export const MAIN_INFO_FIELDS = [
  'doc_type_id',
  'company_id',
  'department_id',
  'title',
  'owner_employee_id',
] as const

/** Giá trị của ô select khi người dùng chọn "không chọn gì". */
const NONE = 'none'

interface DocumentMainInfoFieldsProps {
  form: UseFormReturn<DocumentRecordFormValues>
  /** Văn bản đã có số hiệu: khóa ô loại và pháp nhân — đổi là hỏng số đã ban hành. */
  isNumbered: boolean
  /** Bỏ chính văn bản đang sửa ra khỏi khối gợi ý "đã có văn bản cùng loại". */
  excludeId?: number
  /** Chỉ trang tạo mới truyền hai props này để hiện ô chọn nội dung mẫu. */
  templateId?: number | null
  onTemplateChange?: (templateId: number | null) => void
}

function Required() {
  return <span className="text-destructive"> *</span>
}

/**
 * THÔNG TIN CHÍNH — bộ trường chung C01.
 *
 * **Tên văn bản đứng đầu** — đó là thứ người soạn đã có sẵn trong đầu khi mở
 * form ra; bắt khai loại và pháp nhân trước là chặn họ ngay ở ô đầu tiên.
 *
 * Sau tên, thứ tự bám theo cái quyết định cái kia: **loại văn bản** và **pháp
 * nhân ban hành** vì hai ô đó quyết định số hiệu (hiện ngay ở dòng xem trước
 * bên dưới) và mức mật mặc định; **phòng chủ trì** kế đó vì nó vào giữa chuỗi
 * số hiệu và là chiều lọc của khối gợi ý văn bản trùng.
 *
 * Dùng chung cho trang tạo mới và tab "Thông tin" của trang chi tiết — hai chỗ
 * đó phải hỏi y hệt nhau, tách ra là sớm muộn cũng lệch.
 */
export function DocumentMainInfoFields({
  form,
  isNumbered,
  excludeId,
  templateId,
  onTemplateChange,
}: DocumentMainInfoFieldsProps) {
  const documentTypes = useActiveDocumentTypes()
  const { data: companies } = useCompanies({ page_size: 200, is_active: true })
  const { data: departments } = useDepartments({ page_size: 500 })
  const { data: employees } = useEmployees({ page_size: 1000, is_active: true })
  const { items: books } = useDocumentBooks()

  const docTypeId = form.watch('doc_type_id')
  const companyId = form.watch('company_id')
  const departmentId = form.watch('department_id')
  const bookId = form.watch('book_id')
  const templates = useActiveDocumentTemplates(docTypeId, Boolean(onTemplateChange))

  const { data: preview, isFetching: dangNapSoHieu } = useNumberPreview({
    doc_type_id: docTypeId,
    company_id: companyId,
    department_id: departmentId,
    book_id: bookId,
  })

  const employeeOptions = employees?.items ?? []
  const departmentOptions = (departments?.items ?? []).filter((item) => item.is_active)

  /** Chọn loại xong thì kéo theo mức mật mặc định của loại đó. */
  function handleTypeChange(value: string) {
    const id = Number(value)
    form.setValue('doc_type_id', id, { shouldValidate: true })
    const picked = documentTypes.find((item) => item.id === id)
    if (picked) form.setValue('secrecy_level', picked.default_secrecy)
    // Mẫu luôn thuộc một loại cụ thể. Đổi loại thì lựa chọn cũ không còn hợp lệ.
    onTemplateChange?.(null)
  }

  return (
    <div className="grid items-start gap-x-5 gap-y-3 sm:grid-cols-2">
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
        name="doc_type_id"
        render={({ field }) => (
          <FormItem>
            <FormLabel>
              Loại văn bản
              <Required />
            </FormLabel>
            <Select
              value={field.value ? String(field.value) : ''}
              onValueChange={handleTypeChange}
              disabled={isNumbered}
            >
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Chọn loại văn bản" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {documentTypes.map((type) => (
                  <SelectItem key={type.id} value={String(type.id)}>
                    {type.code} · {type.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormDescription>
              {isNumbered
                ? 'Không đổi được: văn bản đã cấp số theo loại này.'
                : 'Loại quyết định kiểu số hiệu và mức mật mặc định.'}
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      {onTemplateChange && (
        <FormItem>
          <FormLabel>Văn bản mẫu</FormLabel>
          {/*  KHÔNG khóa ô khi đang nạp — chỉ khóa khi chưa chọn loại. Khóa rồi
               mở lại sau vài trăm mili giây làm ô nhấp nháy xám, và ai vừa bấm
               vào đúng nhịp đó thì bấm hụt. */}
          <Select
            value={templateId ? String(templateId) : NONE}
            onValueChange={(value) => onTemplateChange(value === NONE ? null : Number(value))}
            disabled={!docTypeId}
          >
            <SelectTrigger className="w-full">
              <SelectValue
                placeholder={docTypeId ? 'Chọn văn bản mẫu' : 'Chọn loại văn bản trước'}
              />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={NONE}>-- Không dùng văn bản mẫu --</SelectItem>
              {templates.items.map((template) => (
                <SelectItem key={template.id} value={String(template.id)}>
                  {template.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {/*  `min-h-10` giữ chỗ sẵn hai dòng: bốn câu dưới đây dài ngắn khác
               nhau, đổi câu mà không giữ chỗ thì cả hàng lưới xô lên xuống. */}
          <FormDescription className="min-h-10">
            {!docTypeId
              ? 'Danh sách mẫu được lọc theo loại văn bản.'
              : templates.isError
                ? 'Không tải được danh sách văn bản mẫu.'
                : templates.items.length === 0 && !templates.isFetching
                  ? 'Loại văn bản này chưa có mẫu đang sử dụng.'
                  : 'Nội dung mẫu sẽ được chép vào trang soạn thảo sau khi tạo.'}
          </FormDescription>
        </FormItem>
      )}

      <FormField
        control={form.control}
        name="company_id"
        render={({ field }) => (
          <FormItem>
            <FormLabel>
              Pháp nhân ban hành
              <Required />
            </FormLabel>
            <Select
              value={field.value ? String(field.value) : ''}
              onValueChange={(value) => field.onChange(Number(value))}
              disabled={isNumbered}
            >
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Chọn pháp nhân" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {(companies?.items ?? []).map((company) => (
                  <SelectItem key={company.id} value={String(company.id)}>
                    {company.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormDescription>
              {isNumbered
                ? 'Không đổi được: văn bản đã cấp số theo pháp nhân này.'
                : 'Nơi ĐỨNG TÊN ban hành, không phải nơi của người đang nhập.'}
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="department_id"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Phòng chủ trì</FormLabel>
            <Select
              value={field.value ? String(field.value) : NONE}
              onValueChange={(value) => field.onChange(value === NONE ? null : Number(value))}
            >
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Chọn phòng chủ trì" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value={NONE}>-- Chưa chọn --</SelectItem>
                {departmentOptions.map((department) => (
                  <SelectItem key={department.id} value={String(department.id)}>
                    {department.name}
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
        name="book_id"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Vào sổ</FormLabel>
            <Select
              value={field.value ? String(field.value) : NONE}
              onValueChange={(value) => field.onChange(value === NONE ? null : Number(value))}
            >
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Không vào sổ" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value={NONE}>-- Không vào sổ --</SelectItem>
                {books
                  .filter((book) => book.is_active)
                  .map((book) => (
                    <SelectItem key={book.id} value={String(book.id)}>
                      {book.name}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
            {/* Nói rõ vào sổ được thêm cái gì — không thì người dùng bỏ trống cho
                nhanh rồi sau đó thắc mắc vì sao đồng nghiệp không xem được. */}
            <FormDescription>
              Vào sổ thì văn bản được cấp thêm một số thứ tự trong sổ, và{' '}
              <strong>mọi thành viên của sổ đọc được</strong> (người quản lý sổ sửa được).
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      {/* Dòng xem trước số hiệu đứng ngay dưới các ô quyết định ra nó. */}
      <DocumentNumberPreview preview={preview} isFetching={dangNapSoHieu} />

      {/* B05 — hiện luôn văn bản cùng loại cùng phòng đang hiệu lực. Đây là thứ
          còn lại chống đẻ trùng quy trình sau khi bước xin phép bị cắt. */}
      <DocumentSuggestionList
        docTypeId={docTypeId}
        departmentId={departmentId}
        companyId={companyId}
        excludeId={excludeId}
      />

      <FormField
        control={form.control}
        name="owner_employee_id"
        render={({ field }) => (
          <FormItem>
            <FormLabel>
              Người chịu trách nhiệm nội dung
              <Required />
            </FormLabel>
            <Select
              value={field.value ? String(field.value) : ''}
              onValueChange={(value) => field.onChange(Number(value))}
            >
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Chọn người chịu trách nhiệm" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {employeeOptions.map((employee) => (
                  <SelectItem key={employee.id} value={String(employee.id)}>
                    {employee.full_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormDescription>
              Người trả lời khi có ai hỏi về văn bản này — khác người ngồi gõ.
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="drafter_employee_id"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Người soạn</FormLabel>
            <Select
              value={field.value ? String(field.value) : NONE}
              onValueChange={(value) => field.onChange(value === NONE ? null : Number(value))}
            >
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Chọn người soạn" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value={NONE}>-- Chưa chọn --</SelectItem>
                {employeeOptions.map((employee) => (
                  <SelectItem key={employee.id} value={String(employee.id)}>
                    {employee.full_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormMessage />
          </FormItem>
        )}
      />
    </div>
  )
}
