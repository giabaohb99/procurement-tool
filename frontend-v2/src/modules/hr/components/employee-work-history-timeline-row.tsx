import { Pencil, PlayCircle, Trash2 } from 'lucide-react'

import { WORK_EVENT_TYPE, labelOf } from '@/shared/constants/statuses'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import type { EmployeeWorkHistoryRowActions } from '../config/employee-work-history-columns'
import { renderFileCell } from '../config/employee-work-history-columns'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import {
  workHistoryBadgeVariant,
  workHistorySummaryLine,
  workHistoryTimelineDateLabel,
  type WorkHistoryTimelineVariant,
} from '../utils/employee-work-history-display'

interface EmployeeWorkHistoryTimelineRowProps {
  row: EmployeeWorkHistory
  variant: WorkHistoryTimelineVariant
  canOpenFiles: boolean
  onOpenFiles: (row: EmployeeWorkHistory) => void
  /** Bỏ trống = chỉ đọc (khu Quyết định bổ nhiệm, và /me) — KHÔNG cột Thao tác. */
  actions?: EmployeeWorkHistoryRowActions
}

/**
 * Nội dung MỘT mốc của dòng thời gian — tách khỏi `employee-work-history-timeline.tsx`
 * để tệp đó gọn, chỉ lo sắp xếp + khung `<ol>`.
 *
 * Thao tác (Sửa/Áp/Xóa) tái dùng ĐÚNG các hàm trong `actions` mà bảng đang
 * dùng (`buildEmployeeWorkHistoryColumns`) — không viết lại luồng xác nhận.
 */
export function EmployeeWorkHistoryTimelineRow({
  row,
  variant,
  canOpenFiles,
  onOpenFiles,
  actions,
}: EmployeeWorkHistoryTimelineRowProps) {
  const summary = workHistorySummaryLine(row)

  return (
    <div className="-mt-0.5 flex flex-wrap items-start justify-between gap-3">
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium">{workHistoryTimelineDateLabel(row, variant)}</span>
          <Badge variant={workHistoryBadgeVariant(row.event_type)}>
            {labelOf(WORK_EVENT_TYPE, String(row.event_type))}
          </Badge>
          {row.is_current && <Badge variant="secondary">Hiện tại</Badge>}
        </div>

        {summary && <p className="text-sm text-muted-foreground">{summary}</p>}

        {row.decision_no && (
          <p className="text-xs text-muted-foreground">Số QĐ: {row.decision_no}</p>
        )}

        {row.note && <p className="text-xs whitespace-pre-wrap text-muted-foreground">{row.note}</p>}
      </div>

      <div className="flex shrink-0 items-center gap-1">
        {renderFileCell({ row, canOpenFiles, onOpenFiles })}

        {actions && (
          <>
            <Button type="button" variant="ghost" size="icon-sm" title="Sửa" onClick={() => actions.onEdit(row)}>
              <Pencil />
            </Button>
            {row.can_apply && (
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                title="Áp vào hồ sơ"
                disabled={actions.isApplying(row)}
                onClick={() => actions.onApply(row)}
              >
                <PlayCircle />
              </Button>
            )}
            <ConfirmIconButton
              icon={Trash2}
              title="Xóa"
              confirmTitle="Xóa dòng quá trình công tác?"
              confirmDescription="Thao tác này không hoàn tác được. Tệp QĐ đính kèm (nếu có) cũng bị xóa theo."
              destructive
              disabled={actions.isDeleting(row)}
              onConfirm={() => actions.onDelete(row)}
            />
          </>
        )}
      </div>
    </div>
  )
}
