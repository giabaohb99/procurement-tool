import { Building2, UserRoundPen } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'

import { RETURN_TARGET_LABELS, type ReturnTarget } from '../utils/return-action'

/**
 * Hộp hỏi «Trả về đâu?» — bao-CR-498. Chỉ mở khi phiếu đang mở CẢ HAI đường trả
 * (`resolveReturnAction` trả `choose`); một đường thì nút «Trả về» đi thẳng, không hỏi.
 */
interface ReturnChoiceDialogProps {
  open: boolean
  /** Tên chứng từ để đọc trong câu: «yêu cầu mua hàng», «yêu cầu báo giá». */
  docLabel: string
  onOpenChange: (open: boolean) => void
  onPick: (target: ReturnTarget) => void
}

export function ReturnChoiceDialog({ open, docLabel, onOpenChange, onPick }: ReturnChoiceDialogProps) {
  function pick(target: ReturnTarget) {
    onOpenChange(false)
    onPick(target)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Trả {docLabel} về đâu?</DialogTitle>
          <DialogDescription>
            Phiếu này đang mở cả hai đường trả. Chọn một đường, bước sau sẽ hỏi lý do.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-2">
          {(['requester', 'department'] as const).map((target) => {
            const meta = RETURN_TARGET_LABELS[target]
            const Icon = target === 'requester' ? UserRoundPen : Building2
            return (
              <button
                key={target}
                type="button"
                onClick={() => pick(target)}
                className="flex items-start gap-3 rounded-md border p-3 text-left hover:bg-accent"
              >
                <Icon className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                <span>
                  <span className="block text-sm font-medium">{meta.title}</span>
                  <span className="block text-xs text-muted-foreground">{meta.description}</span>
                </span>
              </button>
            )
          })}
        </div>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
