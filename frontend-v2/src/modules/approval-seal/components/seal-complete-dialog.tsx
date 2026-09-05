import { CheckCircle2, X } from 'lucide-react'
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

interface SealCompleteDialogProps {
  code: string
  pending?: boolean
  onConfirm: (payload: { note: string }) => void
  onClose: () => void
}

/**
 * Văn thư HOÀN THÀNH đóng dấu: ghi chú BẮT BUỘC. Theo C-01: chỉ đóng bằng Hủy / X,
 * chặn Esc + nền, hỏi nếu đã nhập dở.
 */
export function SealCompleteDialog({ code, pending, onConfirm, onClose }: SealCompleteDialogProps) {
  const [note, setNote] = useState('')
  const [error, setError] = useState('')

  const dirty = note.trim() !== ''

  async function attemptClose() {
    if (pending) return
    if (dirty && !(await confirm({ message: 'Bạn đã nhập nội dung. Đóng và bỏ nội dung này?' }))) return
    onClose()
  }

  function handleConfirm() {
    if (!note.trim()) {
      setError('Vui lòng nhập ghi chú hoàn thành.')
      return
    }
    setError('')
    onConfirm({ note: note.trim() })
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
            <DialogTitle>Hoàn thành đóng dấu {code}</DialogTitle>
            <DialogDescription>Ghi chú bàn giao sau khi đã đóng dấu.</DialogDescription>
          </div>
          <Button type="button" variant="ghost" size="icon" onClick={attemptClose} aria-label="Đóng">
            <X className="size-4" />
          </Button>
        </DialogHeader>

        <div className="flex flex-col gap-4 py-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="seal-complete-note">
              Ghi chú
              <RequiredMark />
            </Label>
            <Textarea
              id="seal-complete-note"
              rows={3}
              value={note}
              placeholder="VD: Đã đóng dấu và bàn giao cho người yêu cầu."
              onChange={(e) => setNote(e.target.value)}
            />
            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
        </div>

        <div className="flex items-center justify-end gap-2">
          <Button variant="ghost" onClick={attemptClose} disabled={pending}>
            Hủy
          </Button>
          <Button onClick={handleConfirm} disabled={pending}>
            <CheckCircle2 className="size-4" />
            Hoàn thành
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
