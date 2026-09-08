import { Check, X } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Label } from '@/shared/ui/label'

interface SealApproveDialogProps {
  /** Tiêu đề hộp thoại (mục đích / mã phiếu). */
  subject: string
  pending?: boolean
  onConfirm: () => void
  onClose: () => void
}

/**
 * Hộp thoại XÁC NHẬN PHÊ DUYỆT phiếu đóng dấu (yêu cầu 07/09/2026).
 *
 * **Bắt buộc tick** "đã xem & hiểu nội dung" trước khi bấm Duyệt — nút Duyệt khóa tới khi
 * tick, để người duyệt không bấm duyệt theo quán tính mà chưa đọc phiếu. Đây chỉ là chốt
 * ở giao diện; backend vẫn kiểm trạng thái + quyền như thường.
 */
export function SealApproveDialog({ subject, pending, onConfirm, onClose }: SealApproveDialogProps) {
  const [confirmed, setConfirmed] = useState(false)

  return (
    <Dialog
      open
      onOpenChange={(next) => {
        if (!next) onClose()
      }}
    >
      <DialogContent showCloseButton={false} className="sm:max-w-[600px]">
        <DialogHeader className="flex-row items-start justify-between text-left">
          <div>
            <DialogTitle>{`Phê duyệt "${subject}"`}</DialogTitle>
            <DialogDescription>Xác nhận trước khi phê duyệt yêu cầu đóng dấu này.</DialogDescription>
          </div>
          <Button type="button" variant="ghost" size="icon" onClick={onClose} aria-label="Đóng">
            <X className="size-4" />
          </Button>
        </DialogHeader>

        {/*  Cả ô bấm được để tick — Radix Checkbox là <button> nên `label htmlFor` KHÔNG tự
            toggle; tự xử lý onClick trên cả hàng cho chắc (click chữ cũng tick). */}
        <div
          className="flex cursor-pointer items-start gap-3 rounded-md border bg-muted/30 p-3"
          onClick={() => setConfirmed((c) => !c)}
        >
          <Checkbox checked={confirmed} className="pointer-events-none mt-0.5" tabIndex={-1} />
          <Label className="cursor-pointer text-sm font-normal leading-snug">
            Tôi xác nhận đã xem và hiểu nội dung của yêu cầu này, đồng ý thực hiện phê duyệt theo
            thẩm quyền của mình.
          </Label>
        </div>

        <div className="flex items-center justify-end gap-2">
          <Button variant="ghost" onClick={onClose} disabled={pending}>
            Hủy
          </Button>
          {/*  Khóa Duyệt tới khi tick xác nhận. */}
          <Button onClick={onConfirm} disabled={pending || !confirmed}>
            <Check className="size-4" />
            Duyệt
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
