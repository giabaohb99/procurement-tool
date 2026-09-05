import { CheckCircle2, X } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { confirm } from '@/shared/ui/confirm-dialog'

interface BookingCompleteDialogProps {
  code: string
  pending?: boolean
  onConfirm: (payload: { distance_km?: number; cost?: number }) => void
  onClose: () => void
}

/**
 * Tài xế HOÀN TẤT chuyến: ghi số km + chi phí thực tế (đều tùy chọn — để trống thì
 * giữ nguyên). Theo C-01: chỉ đóng bằng Hủy / X, chặn Esc + nền, hỏi nếu đã nhập dở.
 */
export function BookingCompleteDialog({ code, pending, onConfirm, onClose }: BookingCompleteDialogProps) {
  const [km, setKm] = useState('')
  const [cost, setCost] = useState('')

  const dirty = km.trim() !== '' || cost.trim() !== ''

  async function attemptClose() {
    if (pending) return
    if (dirty && !(await confirm({ message: 'Bạn đã nhập số liệu. Đóng và bỏ nội dung này?' }))) return
    onClose()
  }

  function handleConfirm() {
    onConfirm({
      distance_km: km.trim() === '' ? undefined : Number(km),
      cost: cost.trim() === '' ? undefined : Number(cost),
    })
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
            <DialogTitle>Hoàn tất chuyến {code}</DialogTitle>
            <DialogDescription>Ghi số km và chi phí thực tế (có thể để trống).</DialogDescription>
          </div>
          <Button type="button" variant="ghost" size="icon" onClick={attemptClose} aria-label="Đóng">
            <X className="size-4" />
          </Button>
        </DialogHeader>

        <div className="grid grid-cols-2 gap-4 py-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="booking-km">Số km</Label>
            <Input
              id="booking-km"
              type="number"
              min={0}
              inputMode="decimal"
              value={km}
              onChange={(e) => setKm(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="booking-cost">Chi phí (đ)</Label>
            <Input
              id="booking-cost"
              type="number"
              min={0}
              inputMode="numeric"
              value={cost}
              onChange={(e) => setCost(e.target.value)}
            />
          </div>
        </div>

        <div className="flex items-center justify-end gap-2">
          <Button variant="ghost" onClick={attemptClose} disabled={pending}>
            Hủy
          </Button>
          <Button onClick={handleConfirm} disabled={pending}>
            <CheckCircle2 className="size-4" />
            Hoàn tất chuyến
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
