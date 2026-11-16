import { CopyPlus, X } from 'lucide-react'

import { Button } from '@/shared/ui/button'

interface WorkRosterShiftActionsProps {
  selectedCount: number
  onClearSelection: () => void
  onCopyWeek: () => void
  /** Không có dòng nào sửa được trên trang → nút chép tắt. */
  disabled: boolean
}

/**
 * Nút xếp ca trên thanh công cụ Xem lịch (duoc-CR-761, chỉ ở chế độ TUẦN): số dòng đang chọn + Bỏ chọn, và
 * "Chép tuần trước". Không chọn dòng nào thì chép cho mọi dòng sửa được trên trang.
 */
export function WorkRosterShiftActions({ selectedCount, onClearSelection, onCopyWeek, disabled }: WorkRosterShiftActionsProps) {
  return (
    <>
      {selectedCount > 0 && (
        <span className="flex items-center gap-1 text-sm text-muted-foreground">
          Đã chọn <strong className="text-foreground tabular-nums">{selectedCount}</strong>
          <Button type="button" variant="ghost" size="icon-sm" aria-label="Bỏ chọn" onClick={onClearSelection}>
            <X className="size-4" />
          </Button>
        </span>
      )}
      <Button type="button" variant="outline" size="sm" disabled={disabled} onClick={onCopyWeek}>
        <CopyPlus className="size-4" />
        Chép tuần trước
      </Button>
    </>
  )
}
