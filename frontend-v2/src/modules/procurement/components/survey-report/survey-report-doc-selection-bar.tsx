// duoc-CR-611 (07/10/2026) — thanh «chọn nhiều» trong dải sổ của MỘT dòng hàng (dạng xem
// theo dòng hàng của khối Báo cáo thực hiện): chọn tất cả / bỏ chọn, đếm số đã chọn, xóa
// các hồ sơ đã chọn một lượt. Tách khỏi `survey-report-card.tsx` (đã >1.600 dòng).
import { ListChecks, Trash2, X } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'

interface SurveyReportDocSelectionBarProps {
  /** Đang ở chế độ chọn chưa — chưa thì chỉ bày nút «Chọn nhiều». */
  selecting: boolean
  /** Số hồ sơ đang bày trong dải (đã qua bộ lọc) — mẫu số của «chọn tất cả». */
  total: number
  /** Số hồ sơ đang bày VÀ đang được chọn. */
  selectedCount: number
  busy: boolean
  onStart: () => void
  onToggleAll: (checked: boolean) => void
  onDeleteSelected: () => void
  onCancel: () => void
}

export function SurveyReportDocSelectionBar({
  selecting,
  total,
  selectedCount,
  busy,
  onStart,
  onToggleAll,
  onDeleteSelected,
  onCancel,
}: SurveyReportDocSelectionBarProps) {
  if (!selecting) {
    return (
      <Button type="button" variant="outline" size="sm" disabled={busy || total === 0} onClick={onStart}>
        <ListChecks />
        Chọn nhiều
      </Button>
    )
  }

  const allChecked = total > 0 && selectedCount === total
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-lg border bg-card px-3 py-1.5">
      <label className="flex cursor-pointer items-center gap-2 text-sm">
        <Checkbox
          aria-label="Chọn tất cả hồ sơ của dòng hàng này"
          checked={allChecked ? true : selectedCount > 0 ? 'indeterminate' : false}
          onCheckedChange={(checked) => onToggleAll(checked === true)}
        />
        Chọn tất cả
      </label>
      <span className="text-xs text-muted-foreground tabular-nums">
        Đã chọn {selectedCount}/{total}
      </span>
      <div className="ml-auto flex items-center gap-2">
        <Button
          type="button"
          variant="destructive"
          size="sm"
          disabled={busy || selectedCount === 0}
          onClick={onDeleteSelected}
        >
          <Trash2 />
          Xóa đã chọn{selectedCount > 0 ? ` (${selectedCount})` : ''}
        </Button>
        <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
          <X />
          Bỏ chọn
        </Button>
      </div>
    </div>
  )
}
