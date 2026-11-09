import { Check } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { formatQuantity } from '@/shared/utils/format-money'
import type { SurveyProcessLine } from '../types/survey-request-process'

interface SurveyRequestProcessEmptyLinesDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Dòng của mình, chưa chốt, chưa có phương án nào. */
  emptyLines: SurveyProcessLine[]
  checkedLineIds: number[]
  onCheckedLineIdsChange: (ids: number[]) => void
  pending: boolean
  onConfirm: () => void
}

/**
 * Hộp *Chốt rỗng sản phẩm chưa có phương án* khi bấm *Chốt hoàn thành khảo sát* mà còn dòng
 * chưa gắn phương án — tiêu đề, câu giải thích và hai nút lấy nguyên văn bản v1
 * (`SurveyRequestProcess.tsx`, duoc-CR-741): *Hủy* · *Chốt (n chốt rỗng)*.
 *
 * Nút chốt chỉ bấm được khi đã tick ĐỦ mọi dòng rỗng: dòng không tick mà chưa có phương án
 * thì backend chặn chốt, nên để bấm chỉ tổ ăn một lỗi đỏ.
 */
export function SurveyRequestProcessEmptyLinesDialog({
  open,
  onOpenChange,
  emptyLines,
  checkedLineIds,
  onCheckedLineIdsChange,
  pending,
  onConfirm,
}: SurveyRequestProcessEmptyLinesDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Chốt rỗng sản phẩm chưa có phương án</DialogTitle>
          <DialogDescription>
            Các sản phẩm sau <b>chưa có phương án</b>. Tick những sản phẩm{' '}
            <b>không tìm được NCC phù hợp</b> để <b>chốt rỗng</b> (coi như không có phương án).
            Sản phẩm KHÔNG tick + chưa có phương án sẽ chặn chốt (cần khảo sát tiếp).
          </DialogDescription>
        </DialogHeader>

        <ul className="max-h-[48dvh] space-y-2 overflow-y-auto">
          {emptyLines.map((line) => (
            <li key={line.id} className="flex items-start gap-3 rounded-lg border px-3 py-2">
              <Checkbox
                id={`empty-line-${line.id}`}
                checked={checkedLineIds.includes(line.id)}
                onCheckedChange={(checked) =>
                  onCheckedLineIdsChange(
                    checked === true
                      ? [...checkedLineIds, line.id]
                      : checkedLineIds.filter((id) => id !== line.id),
                  )
                }
              />
              <label htmlFor={`empty-line-${line.id}`} className="text-sm">
                <span className="font-medium">
                  {line.requirement_detail || line.item_group || '—'}
                </span>
                <span className="block text-xs text-muted-foreground">
                  Phân loại: {line.item_group || '—'} · SL: {formatQuantity(line.request_qty) || '—'}{' '}
                  {line.uom}
                </span>
              </label>
            </li>
          ))}
        </ul>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button
            type="button"
            disabled={checkedLineIds.length !== emptyLines.length || pending}
            onClick={onConfirm}
          >
            <Check />
            Chốt ({checkedLineIds.length} chốt rỗng)
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
