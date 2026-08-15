import { Activity, Info, Layers } from 'lucide-react'
import type { ReactNode } from 'react'
import type { UseFormReturn } from 'react-hook-form'

import { Form } from '@/shared/ui/form'
import { FormCard } from '@/shared/ui/form-card'
import { DocumentExtraInfoFields } from './document-extra-info-fields'
import { DocumentMainInfoFields } from './document-main-info-fields'
import { DocumentProcessingFields } from './document-processing-fields'
import type { DocumentRecordFormValues } from '../schemas/document-record-schema'

interface DocumentRecordFormProps {
  formId: string
  form: UseFormReturn<DocumentRecordFormValues>
  /** Đang sửa: KHÓA ô luồng vì số vào sổ đã cấp theo luồng cũ. */
  isEditing: boolean
  onSubmit: (values: DocumentRecordFormValues) => void
  children?: ReactNode
}

/**
 * Form xem lại / sửa toàn bộ thông tin của một văn bản — nội dung của tab
 * "Thông tin" ở trang chi tiết.
 *
 * Cùng ba khối trường mà trang tạo mới hỏi qua hai bước, ở đây gộp lại một
 * trang: lúc sửa thì người dùng đã biết mình cần sửa ô nào, bắt bấm "Tiếp tục"
 * để tới ô đó chỉ tổ mất công.
 */
export function DocumentRecordForm({
  formId,
  form,
  isEditing,
  onSubmit,
  children,
}: DocumentRecordFormProps) {
  return (
    <Form {...form}>
      <form id={formId} onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormCard title="Thông tin chính" icon={Info} iconClassName="text-primary">
          <DocumentMainInfoFields form={form} isEditing={isEditing} />
        </FormCard>

        {/* Cùng thứ tự và cùng biểu tượng với ba bước của trang tạo mới — đảo đi
            thì người dùng phải dò lại xem ô mình vừa khai nằm ở đâu. */}
        <FormCard title="Tình trạng xử lý" icon={Activity} iconClassName="text-violet-500">
          <DocumentProcessingFields form={form} isEditing={isEditing} />
        </FormCard>

        <FormCard title="Thông tin bổ sung" icon={Layers} iconClassName="text-emerald-600">
          <DocumentExtraInfoFields form={form} isEditing={isEditing} />
        </FormCard>

        {/* Trường động + tệp đính kèm nằm trong cùng thẻ `<form>` để nút Lưu
            trên header gom được tất cả. */}
        {children}
      </form>
    </Form>
  )
}
