import { useRef, type ReactNode } from 'react'

import { useIsMobile } from '@/shared/hooks/use-mobile'
import { Dialog, DialogContent } from '@/shared/ui/dialog'
import { Sheet, SheetContent } from '@/shared/ui/sheet'

interface WorkShiftModalProps {
  open: boolean
  onClose: () => void
  children: ReactNode
}

/**
 * Khung của hộp xếp ca (duoc-CR-761, đại ca chốt 16/11/2026): màn rộng là hộp giữa màn `max-w-lg`, cao tối đa 90% màn
 * (mở mục "Áp cùng ca" ra dài thì thân cuộn, chân hộp vẫn thấy — bản trước hộp tràn khỏi màn, mất nút Lưu); khổ điện thoại là
 * tấm trượt từ dưới lên (cao tối đa 90% màn, thân cuộn, chân dính). Con bên trong tự chia đầu / thân / chân.
 *
 * Lúc mở KHÔNG tự đặt con trỏ vào nút đầu tiên (đại ca chê vòng xanh quanh "Đóng"): đặt vào chính khung hộp
 * (`tabIndex=-1` của Radix), bàn phím vẫn Tab vào được như thường.
 */
export function WorkShiftModal({ open, onClose, children }: WorkShiftModalProps) {
  const isMobile = useIsMobile()
  const content = useRef<HTMLDivElement>(null)
  const focusContainer = (event: Event) => {
    event.preventDefault()
    content.current?.focus()
  }
  const onOpenChange = (next: boolean) => {
    if (!next) onClose()
  }

  if (isMobile) {
    return (
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent
          ref={content}
          side="bottom"
          onOpenAutoFocus={focusContainer}
          className="max-h-[90dvh] gap-0 rounded-t-xl p-0 outline-none"
        >
          {children}
        </SheetContent>
      </Sheet>
    )
  }
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent ref={content} onOpenAutoFocus={focusContainer} className="flex max-h-[min(90dvh,52rem)] flex-col gap-0 p-0 sm:max-w-lg">
        {children}
      </DialogContent>
    </Dialog>
  )
}
