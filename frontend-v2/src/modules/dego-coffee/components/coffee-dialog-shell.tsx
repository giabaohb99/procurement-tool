import { X } from 'lucide-react'
import type { ReactNode } from 'react'

import { Button } from '@/shared/ui/button'
import { confirm } from '@/shared/ui/confirm-dialog'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'

interface CoffeeDialogShellProps {
  title: string
  description?: string
  /** Form đang có dữ liệu gõ dở — đóng phải hỏi xác nhận (case UI C-01). */
  dirty: boolean
  pending?: boolean
  confirmLabel: string
  onConfirm: () => void
  onClose: () => void
  children: ReactNode
  widthClass?: string
}

/**
 * Vỏ dialog chung của phân hệ Điểm cà phê, theo case UI C-01: chỉ đóng bằng nút
 * Hủy / X; chặn Esc + click nền; form dở thì hỏi trước khi bỏ.
 */
export function CoffeeDialogShell({
  title,
  description,
  dirty,
  pending,
  confirmLabel,
  onConfirm,
  onClose,
  children,
  widthClass = 'sm:max-w-[520px]',
}: CoffeeDialogShellProps) {
  async function attemptClose() {
    if (pending) return
    if (dirty && !(await confirm({ message: 'Bạn đang nhập dở. Đóng và bỏ nội dung này?' })))
      return
    onClose()
  }

  return (
    <Dialog
      open
      onOpenChange={(next) => {
        if (!next) void attemptClose()
      }}
    >
      <DialogContent
        showCloseButton={false}
        onEscapeKeyDown={(e) => e.preventDefault()}
        onInteractOutside={(e) => e.preventDefault()}
        onPointerDownOutside={(e) => e.preventDefault()}
        className={widthClass}
      >
        <DialogHeader className="flex-row items-start justify-between text-left">
          <div>
            <DialogTitle>{title}</DialogTitle>
            {description && <DialogDescription>{description}</DialogDescription>}
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => void attemptClose()}
            aria-label="Đóng"
          >
            <X className="size-4" />
          </Button>
        </DialogHeader>

        <div className="flex flex-col gap-4 py-2">{children}</div>

        <div className="flex items-center justify-end gap-2">
          <Button variant="ghost" onClick={() => void attemptClose()} disabled={pending}>
            Hủy
          </Button>
          <Button onClick={onConfirm} disabled={pending}>
            {confirmLabel}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
