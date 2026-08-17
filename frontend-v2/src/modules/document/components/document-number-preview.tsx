import { Hash } from 'lucide-react'

import { FormDescription, FormItem, FormLabel } from '@/shared/ui/form'
import { cn } from '@/shared/utils/cn'
import type { NumberPreview } from '../types/document-record'

interface DocumentNumberPreviewProps {
  preview?: NumberPreview
  /** Đang nạp số mới trong khi vẫn bày số cũ — làm mờ để không ai đọc nhầm. */
  isFetching?: boolean
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
export function DocumentNumberPreview({ preview, isFetching }: DocumentNumberPreviewProps) {
  return (
    <FormItem>
      <FormLabel>Số hiệu</FormLabel>
      {/*  `h-9` cố định: ô này không phải ô nhập nhưng nằm cùng lưới với các ô
           nhập, cao bằng chúng thì đổi nội dung bên trong cũng không xô hàng. */}
      <div
        aria-busy={isFetching}
        className={cn(
          'flex h-9 items-center gap-2 rounded-md border border-dashed px-3 text-sm transition-opacity',
          isFetching && 'opacity-50',
        )}
      >
        <Hash className="size-4 shrink-0 text-muted-foreground" />
        <span className="truncate font-medium tabular-nums">
          {preview?.preview || 'Chọn loại và pháp nhân để xem số'}
        </span>
      </div>
      {/*  Hai câu chú thích dài gần bằng nhau và khối giữ chiều cao tối thiểu
           hai dòng: đổi câu giữa chừng mà lưới không xô. */}
      <FormDescription className="min-h-10">
        {preview?.number_when === 1
          ? 'Số cấp ngay khi lưu bản nháp.'
          : 'Số thật được cấp lúc văn bản được duyệt — con số trên chỉ là xem trước.'}
      </FormDescription>
    </FormItem>
  )
}
