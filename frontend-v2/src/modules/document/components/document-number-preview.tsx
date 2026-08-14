import { Hash } from 'lucide-react'

import { FormDescription, FormItem, FormLabel } from '@/shared/ui/form'
import type { NumberPreview } from '../types/document-record'

interface DocumentNumberPreviewProps {
  preview?: NumberPreview
}

/**
 * XEM TRƯỚC số hiệu (D08) — **không phải ô nhập**.
 *
 * Số hiệu do backend cấp trong cùng giao dịch ghi bản ghi, khóa dòng bộ đếm.
 * Con số ở đây chỉ để người soạn biết văn bản của mình sắp mang số nào; nó lệch
 * được nếu có người khác được cấp số ngay sau khi màn hình đọc xong — nên câu
 * chú thích bên dưới nói thẳng điều đó thay vì để người dùng tưởng số đã là của
 * mình.
 */
export function DocumentNumberPreview({ preview }: DocumentNumberPreviewProps) {
  return (
    <FormItem>
      <FormLabel>Số hiệu</FormLabel>
      <div className="flex h-9 items-center gap-2 rounded-md border border-dashed px-3 text-sm">
        <Hash className="size-4 shrink-0 text-muted-foreground" />
        <span className="truncate font-medium tabular-nums">
          {preview?.preview || 'Chọn loại và pháp nhân để xem số'}
        </span>
      </div>
      <FormDescription>
        {preview?.number_when === 1
          ? 'Số cấp ngay khi lưu bản nháp.'
          : 'Số thật được cấp lúc văn bản được duyệt — con số trên chỉ là xem trước.'}
      </FormDescription>
    </FormItem>
  )
}
