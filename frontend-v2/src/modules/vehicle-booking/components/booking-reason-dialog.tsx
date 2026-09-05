import { X } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Label } from '@/shared/ui/label'
import { RequiredMark } from '@/shared/ui/required-mark'
import { Textarea } from '@/shared/ui/textarea'
import { confirm } from '@/shared/ui/confirm-dialog'

interface BookingReasonDialogProps {
  title: string
  description: string
  /** Nhãn ô nhập lý do. */
  label: string
  placeholder?: string
  confirmLabel: string
  /** Nút xác nhận màu cảnh báo (từ chối) hay thường (yêu cầu chỉnh sửa). */
  destructive?: boolean
  pending?: boolean
  onConfirm: (reason: string) => void
  onClose: () => void
}

/**
 * Dialog nhập LÝ DO cho các bước lùi/chặn (từ chối · yêu cầu chỉnh sửa · tài xế từ
 * chối). Lý do BẮT BUỘC — người nhận phiếu phải biết vì sao bị trả/từ chối.
 *
 * Theo case C-01: chỉ đóng bằng nút Hủy / X; chặn Esc + click nền; đã gõ dở thì
 * hỏi trước khi bỏ.
 */
export function BookingReasonDialog({
  title,
  description,
  label,
  placeholder,
  confirmLabel,
  destructive,
  pending,
  onConfirm,
  onClose,
}: BookingReasonDialogProps) {
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')

  async function attemptClose() {
    if (pending) return
    if (reason.trim() && !(await confirm({ message: 'Bạn đã nhập lý do. Đóng và bỏ nội dung này?' }))) return
    onClose()
  }

  function handleConfirm() {
    if (!reason.trim()) {
      setError('Vui lòng nhập lý do.')
      return
    }
    setError('')
    onConfirm(reason.trim())
  }

  return (
    <Dialog
      open
      onOpenChange={(next) => {
        if (!next) attemptClose()
      }}
    >
      <DialogContent
        showCloseButton={false}
        onEscapeKeyDown={(e) => e.preventDefault()}
        onInteractOutside={(e) => e.preventDefault()}
        onPointerDownOutside={(e) => e.preventDefault()}
        className="sm:max-w-md"
      >
        <DialogHeader className="flex-row items-start justify-between text-left">
          <div>
            <DialogTitle>{title}</DialogTitle>
            <DialogDescription>{description}</DialogDescription>
          </div>
          <Button type="button" variant="ghost" size="icon" onClick={attemptClose} aria-label="Đóng">
            <X className="size-4" />
          </Button>
        </DialogHeader>

        <div className="flex flex-col gap-1.5 py-2">
          <Label htmlFor="booking-reason">
            {label}
            <RequiredMark />
          </Label>
          <Textarea
            id="booking-reason"
            autoFocus
            rows={4}
            value={reason}
            placeholder={placeholder}
            onChange={(e) => setReason(e.target.value)}
          />
          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>

        <div className="flex items-center justify-end gap-2">
          <Button variant="ghost" onClick={attemptClose} disabled={pending}>
            Hủy
          </Button>
          <Button variant={destructive ? 'destructive' : 'default'} onClick={handleConfirm} disabled={pending}>
            {confirmLabel}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
