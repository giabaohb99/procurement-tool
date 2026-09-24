import { X } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { confirm } from '@/shared/ui/confirm-dialog'
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

interface SealReasonDialogProps {
  /** Câu việc, NGẮN và cố định: "Từ chối yêu cầu đóng dấu". */
  title: string
  /** Phiếu đang bị thao tác — mã + trích yếu/mục đích. Dựng riêng, không nhét vào tiêu đề. */
  subject: string
  /** Mã phiếu, đứng trước `subject` cho dễ đối chiếu. Rỗng thì bỏ. */
  code?: string
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
 * Dialog nhập LÝ DO cho các bước lùi/chặn (từ chối · yêu cầu chỉnh sửa). Lý do
 * BẮT BUỘC — người nhận phiếu phải biết vì sao bị trả/từ chối.
 *
 * Theo case C-01: chỉ đóng bằng nút Hủy / X; chặn Esc + click nền; đã gõ dở thì
 * hỏi trước khi bỏ.
 */
export function SealReasonDialog({
  title,
  subject,
  code,
  description,
  label,
  placeholder,
  confirmLabel,
  destructive,
  pending,
  onConfirm,
  onClose,
}: SealReasonDialogProps) {
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
        {/*  ⚠️ Tiêu đề là CÂU VIỆC ngắn, tên phiếu xuống khối riêng bên dưới (đổi
            22/09/2026). Bản trước nhét mục đích vào giữa hai dấu nháy ngay trong
            tiêu đề: mục đích của phiếu đóng dấu thường là cả một câu ("Đóng dấu
            Báo cáo tài chính và báo cáo kiểm toán nộp Cục Thuế và Sở Kế hoạch Đầu
            tư"), nên tiêu đề ăn ba dòng chữ đậm, đẩy ô nhập lý do xuống gần mép
            dưới, và việc PHẢI LÀM — "Từ chối" — chìm ở đầu dòng một. */}
        <DialogHeader className="flex-row items-start justify-between gap-2 space-y-0 text-left">
          <div className="min-w-0">
            <DialogTitle>{title}</DialogTitle>
            <DialogDescription>{description}</DialogDescription>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="-mt-1 shrink-0"
            onClick={attemptClose}
            aria-label="Đóng"
          >
            <X className="size-4" />
          </Button>
        </DialogHeader>

        {/*  Khối nhận diện phiếu: cắt còn 2 dòng — người bấm Từ chối vừa đọc phiếu
            xong, đây chỉ là chỗ xác nhận "đúng phiếu này", không phải chỗ đọc lại. */}
        <div className="rounded-md border bg-muted/40 px-3 py-2">
          {code && <p className="font-mono text-xs font-semibold text-primary">{code}</p>}
          <p className="line-clamp-2 text-sm text-foreground" title={subject}>
            {subject}
          </p>
        </div>

        <div className="flex flex-col gap-1.5 py-2">
          <Label htmlFor="seal-reason">
            {label}
            <RequiredMark />
          </Label>
          <Textarea
            id="seal-reason"
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
