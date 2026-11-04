import { Info } from 'lucide-react'
import { useState, type ReactNode } from 'react'

import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'

interface FormDescriptionHintProps {
  /** `id` mà ô nhập trỏ tới qua `aria-describedby` — phải nằm trên phần CHỮ. */
  id: string
  children: ReactNode
  className?: string
}

/**
 * Chú thích của một ô biểu mẫu THU VÀO biểu tượng (i) ở góc phải hàng nhãn (duoc-CR-708,
 * màn hồ sơ nhân sự kiểu ERPNext). `FormDescription` tự đổi sang dạng này khi nằm trong
 * `FormSectionProvider` có `hints: 'icon'`.
 *
 * - Chuột: rê vào là hiện, rời ra là ẩn. Cảm ứng / bàn phím: chạm hoặc Enter để bật tắt
 *   (Popover chứ không Tooltip — Tooltip của Radix không mở bằng chạm).
 * - Chữ vẫn nằm trong DOM ở dạng `sr-only` mang đúng `id`, nên trình đọc màn hình vẫn đọc
 *   chú thích khi vào ô, như bản hiện dòng.
 * - `type="button"`: nút nằm trong `<form>`, thiếu là bấm (i) thành LƯU hồ sơ.
 *
 * ⚠️ Cần `FormItem` có `relative` (đã có) vì biểu tượng định vị tuyệt đối theo ô.
 */
export function FormDescriptionHint({ id, children, className }: FormDescriptionHintProps) {
  const [open, setOpen] = useState(false)

  return (
    <span data-slot="form-description" className={cn('absolute top-0 right-0', className)}>
      <span id={id} className="sr-only">
        {children}
      </span>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <button
            type="button"
            aria-label="Xem giải thích"
            onPointerEnter={(event) => event.pointerType === 'mouse' && setOpen(true)}
            onPointerLeave={(event) => event.pointerType === 'mouse' && setOpen(false)}
            className="grid size-5 place-items-center rounded-full text-muted-foreground hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
          >
            <Info className="size-3.5" aria-hidden />
          </button>
        </PopoverTrigger>
        <PopoverContent
          side="top"
          align="end"
          //  Không cướp tiêu điểm khỏi ô đang gõ khi mở bằng rê chuột.
          onOpenAutoFocus={(event) => event.preventDefault()}
          className="w-72 p-3 text-xs leading-relaxed text-muted-foreground"
        >
          {children}
        </PopoverContent>
      </Popover>
    </span>
  )
}
