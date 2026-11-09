import { Pencil, PlayCircle, Trash2 } from 'lucide-react'

import { WORK_EVENT_TYPE, labelOf } from '@/shared/constants/statuses'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { formatDate } from '@/shared/utils/format-date'
import {
  renderFileCell,
  type EmployeeWorkHistoryRowActions,
} from '../config/employee-work-history-columns'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import {
  workHistoryOpenEndLabel,
  workHistorySummaryLine,
  type WorkHistoryTimelineVariant,
} from '../utils/employee-work-history-display'

interface WorkHistoryCardProps {
  row: EmployeeWorkHistory
  /** `history` = khu Quá trình công tác (mọi dòng) · `decision` = khu Quyết định bổ nhiệm. */
  variant: WorkHistoryTimelineVariant
  canOpenFiles: boolean
  onOpenFiles: (row: EmployeeWorkHistory) => void
  /** Bỏ trống = chỉ đọc (khu Quyết định, Trang cá nhân) — thẻ không có nút Sửa / Áp / Xóa. */
  actions?: EmployeeWorkHistoryRowActions
  /** "Hôm nay" dạng `YYYY-MM-DD` — truyền vào để nhãn Chưa / Đang hiệu lực kiểm được bằng ngày cố định. */
  today: string
}

/**
 * Khoảng hiệu lực một dòng. Khu Quyết định chỉ có cột "Hiệu lực từ" nên chỉ nói ngày bắt đầu;
 * khu Quá trình nói đủ hai đầu, chưa có ngày kết thúc thì "Từ ..." (nhãn hiệu lực đứng ở dòng đầu).
 */
function describePeriod(row: EmployeeWorkHistory, isDecision: boolean): string {
  const from = formatDate(row.from_date)
  if (isDecision) return `Hiệu lực từ ${from}`
  return row.to_date ? `${from} – ${formatDate(row.to_date)}` : `Từ ${from}`
}

/**
 * Một dòng quá trình công tác / quyết định bổ nhiệm ở khổ điện thoại — dùng CHUNG cho hai khu
 * (cùng kiểu dòng `EmployeeWorkHistory`), xem `DataTableProps.mobileCard`.
 *
 * ⚠️ **Dòng đầu khác nhau theo khu, đúng thứ người đọc dùng để nhận ra bản ghi.** Khu Quyết định
 * đọc theo SỐ QĐ (cột ghim của bảng); khu Quá trình đọc theo LOẠI sự kiện + khoảng hiệu lực, số
 * QĐ tụt xuống dòng phụ màu sky (nhiều dòng không có QĐ nào).
 *
 * ⚠️ **Nút Sửa / Áp / Xóa và nút Tệp là ANH EM của khối chữ.** Bảng không có `onRowClick` nên thẻ
 * là `<div>`, nút đứng ở cột phải; hành vi lấy ĐÚNG các hàm `actions` + `renderFileCell` của bảng
 * (xác nhận xóa, khóa nút khi đang áp, luật A9/Q4 về tệp) — không chép lại luồng nào.
 *
 * Nhãn "Đang / Chưa hiệu lực" theo cùng luật ô Đến ngày của bảng (`workHistoryOpenEndLabel`),
 * không suy từ `to_date` rỗng — nhập bù dòng cũ thì hai dòng cùng rỗng nhưng chỉ một dòng còn hiệu lực.
 */
export function WorkHistoryCard({
  row,
  variant,
  canOpenFiles,
  onOpenFiles,
  actions,
  today,
}: WorkHistoryCardProps) {
  const eventLabel = labelOf(WORK_EVENT_TYPE, String(row.event_type))
  const summary = workHistorySummaryLine(row)
  const openEnd = row.to_date ? null : workHistoryOpenEndLabel(row, today)
  const isDecision = variant === 'decision'

  return (
    <div className="flex items-start gap-2">
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
          <span className="min-w-0 truncate font-medium text-foreground">
            {isDecision ? row.decision_no : eventLabel}
          </span>
          {!isDecision && openEnd && (
            <Badge variant={openEnd === 'Đang hiệu lực' ? 'secondary' : 'outline'}>{openEnd}</Badge>
          )}
        </div>

        {isDecision ? (
          <p className="text-xs text-muted-foreground tabular-nums">
            {eventLabel}
            {row.decision_date && ` · Ký ${formatDate(row.decision_date)}`}
          </p>
        ) : (
          //  Ngày ký hiện cả khi THIẾU số QĐ (dòng nhập bù): bảng có cột Ngày ký QĐ riêng, thẻ không được rơi nó.
          (row.decision_no || row.decision_date) && (
            <p className="truncate text-xs tabular-nums">
              {row.decision_no && (
                <span className="font-mono text-sky-600 dark:text-sky-400">
                  QĐ {row.decision_no}
                </span>
              )}
              {row.decision_date && (
                <span className="text-muted-foreground">
                  {row.decision_no && ' · '}Ký {formatDate(row.decision_date)}
                </span>
              )}
            </p>
          )
        )}

        {summary && <p className="text-sm break-words text-muted-foreground">{summary}</p>}

        <p className="text-xs text-muted-foreground tabular-nums">
          {describePeriod(row, isDecision)}
        </p>

        {!isDecision && row.note && (
          <p className="line-clamp-2 text-xs break-words text-muted-foreground">{row.note}</p>
        )}
        {!isDecision && row.applied_at && (
          <p className="text-xs text-muted-foreground">
            Đã áp vào hồ sơ {formatDate(row.applied_at)}
          </p>
        )}

        {/*  Không có tệp thì bỏ hẳn dòng — dấu "—" của ô bảng ở đây chỉ là một vạch lạc lõng. */}
        {row.file_count > 0 && (
          <div className="-ml-2">{renderFileCell({ row, canOpenFiles, onOpenFiles })}</div>
        )}
      </div>

      {actions && (
        <div className="flex shrink-0 items-start gap-0.5">
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            title="Sửa"
            aria-label="Sửa dòng"
            onClick={() => actions.onEdit(row)}
          >
            <Pencil />
          </Button>
          {row.can_apply && (
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              title="Áp vào hồ sơ"
              aria-label="Áp vào hồ sơ"
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
        </div>
      )}
    </div>
  )
}
