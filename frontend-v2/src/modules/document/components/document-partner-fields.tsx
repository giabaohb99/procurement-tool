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
import { useActiveDocumentPartners } from '../hooks/use-document-catalogs'
import type { DocumentRecordFormValues } from '../schemas/document-record-schema'
import type { DocumentDirection } from '../types/document-record'

interface DocumentPartnerFieldsProps {
  form: UseFormReturn<DocumentRecordFormValues>
  direction: DocumentDirection
}

/**
 * ĐỐI TÁC theo danh mục + NGÀY ĐẾN — chỉ hiện ở trang chi tiết.
 *
 * Lúc tạo mới, nơi nhận đã hỏi bằng danh sách tên tự do (`DocumentRecipientPicker`)
 * nên hỏi thêm ở đây là bắt khai hai lần cùng một thứ. Nhưng sổ văn bản đến vẫn
 * tra theo đối tác trong danh mục và theo ngày đến, nên hai ô này phải sửa được
 * khi rà soát lại.
 */
export function DocumentPartnerFields({ form, direction }: DocumentPartnerFieldsProps) {
  const partners = useActiveDocumentPartners()

  return (
    <>
      {direction !== 'internal' && (
        <FormField
          control={form.control}
          name="partner_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>
                {direction === 'incoming' ? 'Nơi gửi' : 'Nơi nhận (danh mục)'}
              </FormLabel>
              <Select
                value={field.value ? String(field.value) : ''}
                onValueChange={(value) => field.onChange(Number(value))}
              >
                <FormControl>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Chọn đơn vị" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {partners.map((partner) => (
                    <SelectItem key={partner.id} value={String(partner.id)}>
                      {partner.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
      )}

      {direction === 'incoming' && (
        <FormField
          control={form.control}
          name="received_date"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Ngày đến</FormLabel>
              <FormControl>
                <DatePicker value={field.value} onChange={field.onChange} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      )}
    </>
  )
}
