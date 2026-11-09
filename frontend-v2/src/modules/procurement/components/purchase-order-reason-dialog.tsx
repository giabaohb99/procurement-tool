import { Loader2 } from 'lucide-react'
import { useState } from 'react'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Textarea } from '@/shared/ui/textarea'

interface PurchaseOrderReasonDialogProps {
  open: boolean
  title: string
  description: string
  pending?: boolean
  /** Nút xác nhận tô đỏ cho các thao tác khóa đơn / hủy dòng. */
  destructive?: boolean
  /**
   * Chữ nút đồng ý — mang tên chính thao tác như bản v1 (*Trả về*, *Từ chối*, *Hủy duyệt*,
   * *Hủy đơn*, *Tạm ngưng*), duoc-CR-741. Mặc định "Xác nhận" như hộp nhập của v1.
   */
  confirmLabel?: string
  onClose: () => void
  onConfirm: (reason: string) => void | Promise<void>
}

/**
 * Hộp nhập LÝ DO dùng chung cho các thao tác khóa/trả đơn và tạm ngưng/hủy dòng.
 * Lý do là bắt buộc — backend cũng chặn, nên nút xác nhận khóa khi ô còn trống.
 */
export function PurchaseOrderReasonDialog({
  open,
  title,
  description,
  pending,
  destructive,
  confirmLabel = 'Xác nhận',
  onClose,
  onConfirm,
}: PurchaseOrderReasonDialogProps) {
  const [reason, setReason] = useState('')

  // Mở lại hộp thoại cho thao tác khác thì phải sạch ô, không mang lý do cũ theo.
  if (useHasChanged(open)) setReason('')

  return (
    <Dialog open={open} onOpenChange={(next) => !next && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <Textarea
          rows={4}
          value={reason}
          placeholder="Nhập lý do bắt buộc..."
          onChange={(event) => setReason(event.target.value)}
        />
        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose}>
            Hủy
          </Button>
          <Button
            type="button"
            variant={destructive ? 'destructive' : 'default'}
            disabled={!reason.trim() || pending}
            onClick={() => void onConfirm(reason.trim())}
          >
            {pending && <Loader2 className="animate-spin" />}
            {confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
