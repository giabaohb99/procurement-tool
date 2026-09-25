import type { UseFormReturn } from 'react-hook-form'

import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/shared/ui/form'
import { Input } from '@/shared/ui/input'
import { RequiredMark } from '@/shared/ui/required-mark'
import { SearchSelect } from '@/shared/ui/search-select'
import { cn } from '@/shared/utils/cn'
import { useActiveDocumentTypes } from '../hooks/use-document-types'
import type { DocumentRecordFormValues } from '../schemas/document-record-schema'

interface FolderQuickDocumentFieldsProps {
  form: UseFormReturn<DocumentRecordFormValues>
}

type SelectFieldName = 'doc_type_id' | 'company_id' | 'department_id' | 'owner_employee_id'

//  NHÃN TRÁI – Ô PHẢI (mẫu người dùng đưa 25/09/2026): hộp tạo nhanh đọc lướt
//  một lượt từ trên xuống, nhãn cùng một cột thì mắt không phải nhảy dòng.
//  Màn hẹp thì rơi về nhãn trên – ô dưới như mọi form khác.
const ROW = 'gap-x-3 gap-y-1 sm:grid-cols-[9rem_minmax(0,1fr)] sm:items-center'
const MESSAGE = 'sm:col-start-2'

/**
 * Năm ô BẮT BUỘC của văn bản (`MAIN_INFO_FIELDS`) — bản rút gọn cho hộp «Tạo
 * nhanh từ tệp». Cố ý KHÔNG dùng lại `DocumentMainInfoFields`: bộ đó kéo theo
 * văn bản mẫu, sổ, thư mục, số hiệu xem trước, gợi ý văn bản trùng — đúng thứ
 * hộp tạo nhanh muốn bỏ. Ô nào còn thiếu thì khai sau ở tab Thông tin.
 */
export function FolderQuickDocumentFields({ form }: FolderQuickDocumentFieldsProps) {
  const documentTypes = useActiveDocumentTypes()
  const { data: companies } = useCompanies({ page_size: 200, is_active: true })
  const { data: departments } = useDepartments({ page_size: 500 })
  const { data: employees } = useEmployees({ page_size: 1000, is_active: true })

  const options: Record<SelectFieldName, { value: string; label: string }[]> = {
    //  Tên trước, mã sau — cùng thứ tự với form tạo đầy đủ.
    doc_type_id: documentTypes.map((type) => ({
      value: String(type.id),
      label: `${type.name} · ${type.code}`,
    })),
    company_id: (companies?.items ?? []).map((company) => ({
      value: String(company.id),
      label: company.name,
    })),
    department_id: (departments?.items ?? [])
      .filter((item) => item.is_active)
      .map((item) => ({ value: String(item.id), label: item.name })),
    //  Kèm mã nhân viên: công ty có người trùng họ tên.
    owner_employee_id: (employees?.items ?? []).map((employee) => ({
      value: String(employee.id),
      label: employee.code ? `${employee.full_name} · ${employee.code}` : employee.full_name,
    })),
  }

  function handleChange(name: SelectFieldName, value: string) {
    const id = Number(value)
    form.setValue(name, id, { shouldValidate: true })
    //  Chọn loại xong thì kéo theo mức mật mặc định của loại — giống form đầy đủ.
    if (name === 'doc_type_id') {
      const picked = documentTypes.find((item) => item.id === id)
      if (picked) form.setValue('secrecy_level', picked.default_secrecy)
    }
  }

  function renderSelect(name: SelectFieldName, label: string, placeholder: string) {
    return (
      <FormField
        control={form.control}
        name={name}
        render={({ field }) => (
          <FormItem className={ROW}>
            <FormLabel className="gap-0">
              {label}
              <RequiredMark hint="Bắt buộc" />
            </FormLabel>
            <FormControl>
              <SearchSelect
                value={field.value ? String(field.value) : ''}
                onChange={(value) => handleChange(name, value)}
                options={options[name]}
                placeholder={placeholder}
                searchPlaceholder="Gõ để tìm…"
              />
            </FormControl>
            <FormMessage className={MESSAGE} />
          </FormItem>
        )}
      />
    )
  }

  return (
    <div className="space-y-3">
      <p className="text-sm font-semibold">Thông tin chính</p>
      <div className="grid items-start gap-x-8 gap-y-3 lg:grid-cols-2">
        <FormField
          control={form.control}
          name="title"
          render={({ field }) => (
            <FormItem className={cn(ROW, 'lg:col-span-2')}>
              <FormLabel className="gap-0">
                Tên văn bản
                <RequiredMark hint="Bắt buộc" />
              </FormLabel>
              <FormControl>
                <Input placeholder="Tự điền theo tên tệp đầu tiên" {...field} />
              </FormControl>
              <FormMessage className={MESSAGE} />
            </FormItem>
          )}
        />
        {renderSelect('doc_type_id', 'Loại văn bản', 'Chọn loại văn bản')}
        {renderSelect('company_id', 'Pháp nhân', 'Chọn pháp nhân ban hành')}
        {renderSelect('department_id', 'Phòng chủ trì', 'Chọn phòng chủ trì')}
        {renderSelect(
          'owner_employee_id',
          'Người phụ trách',
          'Chọn người chịu trách nhiệm nội dung',
        )}
      </div>
    </div>
  )
}
