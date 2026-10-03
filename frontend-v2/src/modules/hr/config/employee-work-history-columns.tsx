import { Paperclip, Pencil, PlayCircle, Trash2 } from 'lucide-react'

import type { DataTableColumn } from '@/shared/data-table'
import { WORK_EVENT_TYPE, labelOf } from '@/shared/constants/statuses'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { formatDate } from '@/shared/utils/format-date'
import type { EmployeeWorkHistory } from '../types/employee-work-history'

/** Hành động trên mỗi dòng — chỉ dựng cột «Thao tác» khi truyền tham số này. */
export interface EmployeeWorkHistoryRowActions {
  onEdit: (row: EmployeeWorkHistory) => void
  onApply: (row: EmployeeWorkHistory) => void
  onDelete: (row: EmployeeWorkHistory) => void
  isApplying: (row: EmployeeWorkHistory) => boolean
  isDeleting: (row: EmployeeWorkHistory) => boolean
}

interface BuildColumnsOptions {
  /** A9 (Q4) — mở được tệp hay chỉ thấy số lượng. */
  canOpenFiles: boolean
  onOpenFiles: (row: EmployeeWorkHistory) => void
  /** Bỏ trống = không có cột «Thao tác» (dùng ở Trang cá nhân, phase 05). */
  actions?: EmployeeWorkHistoryRowActions
}

/**
 * Ô «Tệp» (Q4) — xem mô tả ba nhánh ở `phase-04` §Thiết kế màn.
 *
 * Xuất ra để dùng lại ở bảng «Quyết định bổ nhiệm»
 * (`employee-work-history-decision-columns.tsx`) và ở dòng thời gian
 * (`employee-work-history-timeline-row.tsx`) — cùng một luật A9/Q4, không chép
 * lại ba nhánh (có tệp+có quyền / có tệp+không quyền / không tệp).
 */
export function renderFileCell({
  row,
  canOpenFiles,
  onOpenFiles,
}: {
  row: EmployeeWorkHistory
  canOpenFiles: boolean
  onOpenFiles: (row: EmployeeWorkHistory) => void
}) {
  if (row.file_count === 0) return <span className="text-muted-foreground">—</span>

  if (!canOpenFiles) {
    //  KHÔNG nút xem/tải, KHÔNG gọi `/api/attachments` — chỉ báo có tệp.
    return (
      <IconTooltip label="Cần quyền xem thông tin nhạy cảm để mở tệp">
        <span className="text-sm text-muted-foreground">Có {row.file_count} tệp đính kèm</span>
      </IconTooltip>
    )
  }

  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      onClick={(event) => {
        event.stopPropagation()
        onOpenFiles(row)
      }}
    >
      <Paperclip className="size-4" />
      {row.file_count}
    </Button>
  )
}

/** Dựng bộ cột của bảng «Quá trình công tác». Dùng lại ở cả tab hồ sơ và Trang cá nhân. */
export function buildEmployeeWorkHistoryColumns({
  canOpenFiles,
  onOpenFiles,
  actions,
}: BuildColumnsOptions): DataTableColumn<EmployeeWorkHistory>[] {
  const columns: DataTableColumn<EmployeeWorkHistory>[] = [
    {
      key: 'from_date',
      header: 'Từ ngày',
      width: 110,
      hideable: false,
      cell: (row) => formatDate(row.from_date),
    },
    {
      key: 'to_date',
      header: 'Đến ngày',
      width: 130,
      cell: (row) =>
        row.to_date ? (
          formatDate(row.to_date)
        ) : (
          <Badge variant="secondary">Đang hiệu lực</Badge>
        ),
    },
    {
      key: 'event_type',
      header: 'Loại',
      width: 140,
      hideable: false,
      cell: (row) => labelOf(WORK_EVENT_TYPE, String(row.event_type)),
    },
    {
      key: 'company_name',
      header: 'Pháp nhân',
      width: 180,
      wrap: true,
      cell: (row) => row.company_name || '—',
    },
    {
      key: 'department_name',
      header: 'Phòng ban',
      width: 180,
      wrap: true,
      cell: (row) => row.department_name || '—',
    },
    {
      key: 'position_label',
      header: 'Chức vụ',
      width: 160,
      wrap: true,
      cell: (row) => row.position_label || '—',
    },
    {
      key: 'decision_no',
      header: 'Số QĐ',
      width: 140,
      cell: (row) => row.decision_no || '—',
    },
    {
      key: 'decision_date',
      header: 'Ngày ký QĐ',
      width: 120,
      cell: (row) => formatDate(row.decision_date) || '—',
    },
    {
      key: 'files',
      header: 'Tệp',
      width: 160,
      cell: (row) => renderFileCell({ row, canOpenFiles, onOpenFiles }),
    },
    {
      key: 'note',
      header: 'Ghi chú',
      width: 220,
      wrap: true,
      defaultHidden: true,
      cell: (row) => row.note || '—',
    },
    {
      key: 'applied_at',
      header: 'Đã áp',
      width: 120,
      defaultHidden: true,
      cell: (row) => formatDate(row.applied_at) || '—',
    },
  ]

  if (!actions) return columns

  columns.push({
    key: 'actions',
    header: 'Thao tác',
    width: 160,
    hideable: false,
    cell: (row) => (
      <div className="flex items-center gap-1" onClick={(event) => event.stopPropagation()}>
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
      </div>
    ),
  })

  return columns
}
