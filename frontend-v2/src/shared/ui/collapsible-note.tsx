import { ChevronDown, Info } from 'lucide-react'
import { useState, type ReactNode } from 'react'

import { useIsMobile } from '@/shared/hooks/use-mobile'
import { cn } from '@/shared/utils/cn'

interface CollapsibleNoteProps {
  /** Câu gọi tên đoạn ghi chú, vd «Lưu ý cách đọc số». */
  title: string
  children: ReactNode
  className?: string
}

/**
 * Đoạn GHI CHÚ CÁCH ĐỌC SỐ của màn báo cáo — **gấp lại ở khổ điện thoại, mở sẵn
 * ở màn rộng**.
 *
 * ⚠️ Không bỏ được những đoạn này: chúng giải thích vì sao hai con số cạnh nhau
 * lại không bằng nhau, hoặc chi phí được chia về dòng hàng theo cách nào — đọc
 * sai cách tính thì con số đúng cũng vô dụng. Nhưng ở 390px mỗi đoạn dài 4-7
 * dòng (≈100-150px) và nằm chắn ngay trên phần số liệu, tức thứ đầu tiên người
 * mở màn nhìn thấy là một đoạn văn. Gấp lại còn một hàng mà vẫn nói được là CÓ
 * lời giải thích ở đây.
 *
 * ⚠️ Rẽ bằng `useIsMobile` chứ không bằng `<details>` + `md:hidden` cho thẻ
 * `<summary>`: người gấp nó lại ở khổ hẹp rồi xoay ngang máy sẽ mắc kẹt — nội
 * dung vẫn bị `details` giấu mà nút mở thì đã `hidden`. Ở màn rộng không có
 * khái niệm đóng.
 */
export function CollapsibleNote({ title, children, className }: CollapsibleNoteProps) {
  const isMobile = useIsMobile()
  const [open, setOpen] = useState(false)
  const showBody = !isMobile || open

  return (
    <div
      className={cn(
        'rounded-lg border bg-muted/40 text-xs leading-relaxed text-muted-foreground print:hidden',
        className,
      )}
    >
      {isMobile && (
        <button
          type="button"
          onClick={() => setOpen((current) => !current)}
          aria-expanded={open}
          className="flex w-full cursor-pointer items-center gap-1.5 px-4 py-3 text-left font-semibold text-foreground"
        >
          <Info className="size-3.5 shrink-0 text-primary" />
          {title}
          <ChevronDown
            className={cn('ml-auto size-4 transition-transform', open && 'rotate-180')}
            aria-hidden="true"
          />
        </button>
      )}

      {showBody && (
        <div className={cn('px-4 pb-3', isMobile ? 'pt-0' : 'pt-3')}>
          {/*  Biểu tượng và nhãn đậm chỉ ở màn RỘNG — khổ hẹp chúng đã nằm trên
               chính cái nút vừa bấm, lặp lại là đọc hai lần một câu. */}
          {!isMobile && (
            <>
              <Info className="mr-1 inline size-3.5 align-[-2px] text-primary" />
              <b>{title}:</b>{' '}
            </>
          )}
          {children}
        </div>
      )}
    </div>
  )
}
