import { CalendarDays, Info, Layers } from 'lucide-react'
import type { ReactNode } from 'react'
import type { UseFormReturn } from 'react-hook-form'

import { Form } from '@/shared/ui/form'
import { FormCard } from '@/shared/ui/form-card'
import { DocumentExtraInfoFields } from './document-extra-info-fields'
import { DocumentLeaveFields } from './document-leave-fields'
import { DocumentMainInfoFields } from './document-main-info-fields'
import type { DocumentRecordFormValues } from '../schemas/document-record-schema'

interface DocumentRecordFormProps {
  formId: string
  form: UseFormReturn<DocumentRecordFormValues>
  /** Đã cấp số: khóa ô loại văn bản và pháp nhân ban hành. */
  isNumbered: boolean
  /** Văn bản đang sửa — bỏ chính nó ra khỏi khối gợi ý văn bản trùng. */
  documentId?: number
  /** Loại là Giấy nghỉ phép: mở thêm thẻ tám ô riêng, lưu vào `metadata`. */
  laNghiPhep?: boolean
  /**
   * Khóa BỘ TRƯỜNG CHUNG (đang trình duyệt). Chỉ khóa hai thẻ trường ở trên —
   * phạm vi áp dụng và chia quyền đọc nằm trong `children` và vẫn sửa được:
   * chúng không phải nội dung mà người duyệt đang đọc.
   */
  readOnly?: boolean
  onSubmit: (values: DocumentRecordFormValues) => void
  children?: ReactNode
}

/**
 * Form xem lại / sửa bộ trường chung của một văn bản — tab "Thông tin" ở trang
 * chi tiết.
 *
 * Cùng hai khối trường mà trang tạo mới hỏi qua hai bước, ở đây gộp một trang:
 * lúc sửa thì người dùng đã biết mình cần sửa ô nào, bắt bấm "Tiếp tục" để tới
 * ô đó chỉ tổ mất công.
 */
export function DocumentRecordForm({
  formId,
  form,
  isNumbered,
  documentId,
  laNghiPhep = false,
  readOnly = false,
  onSubmit,
  children,
}: DocumentRecordFormProps) {
  return (
    <Form {...form}>
      <form id={formId} onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        {/* `fieldset disabled` khóa MỌI ô bên trong bằng đúng cơ chế của trình
            duyệt — chắc hơn là đi truyền `disabled` xuống từng ô rồi quên một ô. */}
        <fieldset disabled={readOnly} className="space-y-4">
          <FormCard title="Thông tin chính" icon={Info} iconClassName="text-primary">
            <DocumentMainInfoFields
              form={form}
              isNumbered={isNumbered}
              excludeId={documentId}
            />
          </FormCard>

          {/* Cùng chỗ, cùng biểu tượng với trang tạo mới. */}
          {laNghiPhep && (
            <FormCard
              title="Thông tin nghỉ phép"
              icon={CalendarDays}
              iconClassName="text-amber-600"
            >
              <DocumentLeaveFields form={form} />
            </FormCard>
          )}

          {/* Cùng thứ tự và cùng biểu tượng với hai bước của trang tạo mới — đảo
              đi thì người dùng phải dò lại xem ô mình vừa khai nằm ở đâu. */}
          <FormCard title="Thông tin bổ sung" icon={Layers} iconClassName="text-emerald-600">
            <DocumentExtraInfoFields form={form} />
          </FormCard>
        </fieldset>

        {/* Tệp đính kèm và bảng chia sẻ nằm trong cùng thẻ `<form>` để nút Lưu
            trên header gom được tất cả. */}
        {children}
      </form>
    </Form>
  )
}
