import { Paperclip, Pencil, Trash2 } from 'lucide-react'

import type { DataTableColumn } from '@/shared/data-table'
import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { formatDate } from '@/shared/utils/format-date'
import type { CellGetters } from '@/shared/utils/sort-rows-by-cell'
import { EmployeeConcurrentStatusBadge } from '../components/employee-concurrent-status-badge'
import { CONCURRENT_ACTIVE, CONCURRENT_UPCOMING, type EmployeeConcurrent } from '../types/employee-concurrent'

/** Hành động trên mỗi dòng — chỉ dựng cột "Thao tác" khi backend cho sửa (`can_edit`). */
export interface EmployeeConcurrentRowActions {
  onEdit: (row: EmployeeConcurrent) => void
  onDelete: (row: EmployeeConcurrent) => void
  isDeleting: (row: EmployeeConcurrent) => boolean
}

interface BuildColumnsOptions {
  canOpenFiles: boolean
  onOpenFiles: (row: EmployeeConcurrent) => void
  actions?: EmployeeConcurrentRowActions
}

/**
 * Giá trị đem xếp — bảng nạp đủ mọi dòng (≤ 30) nên xếp ở trình duyệt (luật §8). Trạng thái xếp theo DÒNG ĐỜI
 * (Sắp tới → Đang hiệu lực → Đã hết), ô trống xuống cuối cả hai chiều.
 */
export const EMPLOYEE_CONCURRENT_SORT_GETTERS: CellGetters<EmployeeConcurrent> = {
  company_name: (row) => row.company_name,
  department_name: (row) => row.department_name,
  position_label: (row) => row.position_label,
  from_date: (row) => row.from_date,
  to_date: (row) => row.to_date,
  status: (row) => row.status,
  counts_scope: (row) => (row.counts_scope ? 1 : 0),
  decision_no: (row) => row.decision_no,
  files: (row) => row.file_count || null,
  note: (row) => row.note,
}

/** Ô "Tệp": không tệp → gạch; có tệp nhưng không được mở → chỉ báo số (không gọi API); được mở → nút mở hộp tệp. */
export function renderConcurrentFileCell(
  row: EmployeeConcurrent,
  canOpenFiles: boolean,
  onOpenFiles: (row: EmployeeConcurrent) => void,
) {
  if (row.file_count === 0) return <span className="text-muted-foreground">—</span>
  if (!canOpenFiles) {
    return (
      <IconTooltip label="Cần quyền xem thông tin nhạy cảm để mở tệp">
        <span className="text-sm text-muted-foreground">Có {row.file_count} tệp</span>
      </IconTooltip>
    )
  }
  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      aria-label={`Mở ${row.file_count} tệp quyết định`}
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

/** Câu xác nhận xóa — dòng đang có tác dụng thì nói rõ người này mất phạm vi phòng đó ngay. */
export function concurrentDeleteDescription(row: EmployeeConcurrent): string {
  const live = row.counts_scope && (row.status === CONCURRENT_ACTIVE || row.status === CONCURRENT_UPCOMING)
  const scope = live ? ' Người này sẽ thôi thấy dữ liệu của phòng này ở công ty này.' : ''
  return `Xóa kiêm nhiệm phòng "${row.department_name}" — ${row.company_name}? Tệp QĐ đính kèm (nếu có) cũng bị xóa.${scope}`
}

export function buildEmployeeConcurrentColumns({
  canOpenFiles,
  onOpenFiles,
  actions,
}: BuildColumnsOptions): DataTableColumn<EmployeeConcurrent>[] {
  const columns: DataTableColumn<EmployeeConcurrent>[] = [
    { key: 'company_name', sortable: true, header: 'Công ty', width: 150, wrap: true, hideable: false,
      cell: (row) => row.company_name || `Công ty #${row.company_id}` },
    { key: 'department_name', sortable: true, header: 'Phòng ban', width: 140, wrap: true, hideable: false,
      cell: (row) => row.department_name || `Phòng #${row.department_id}` },
    { key: 'position_label', sortable: true, header: 'Chức vụ', width: 110, wrap: true,
      cell: (row) => row.position_label || '—' },
    { key: 'from_date', sortable: true, header: 'Từ ngày', width: 95, cell: (row) => formatDate(row.from_date) || '—' },
    { key: 'to_date', sortable: true, header: 'Đến ngày', width: 110, cell: (row) => formatDate(row.to_date) || '—' },
    { key: 'status', sortable: true, header: 'Trạng thái', width: 120,
      cell: (row) => <EmployeeConcurrentStatusBadge row={row} /> },
    { key: 'counts_scope', sortable: true, header: 'Tính phạm vi', width: 115,
      cell: (row) => (row.counts_scope ? 'Có' : 'Không') },
    //  Số + ngày QĐ gộp một ô (số trên, ngày dưới) cho bảng vừa khổ 1440 không phải cuộn ngang; xếp theo SỐ QĐ.
    { key: 'decision_no', sortable: true, header: 'Quyết định', width: 120, wrap: true,
      cell: (row) =>
        row.decision_no || row.decision_date ? (
          <div className="leading-tight">
            <div>{row.decision_no || '—'}</div>
            {row.decision_date && <div className="text-xs text-muted-foreground">{formatDate(row.decision_date)}</div>}
          </div>
        ) : (
          '—'
        ) },
    { key: 'files', sortable: true, header: 'Tệp', width: 70,
      cell: (row) => renderConcurrentFileCell(row, canOpenFiles, onOpenFiles) },
    { key: 'note', sortable: true, header: 'Ghi chú', width: 200, wrap: true, defaultHidden: true,
      cell: (row) => row.note || '—' },
  ]

  if (!actions) return columns

  columns.push({
    key: 'actions',
    header: 'Thao tác',
    width: 90,
    hideable: false,
    cell: (row) => (
      <div className="flex items-center gap-1" onClick={(event) => event.stopPropagation()}>
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          title="Sửa"
          aria-label={`Sửa kiêm nhiệm ${row.department_name}`}
          onClick={() => actions.onEdit(row)}
        >
          <Pencil />
        </Button>
        <ConfirmIconButton
          icon={Trash2}
          title="Xóa"
          confirmTitle="Xóa dòng kiêm nhiệm?"
          confirmDescription={concurrentDeleteDescription(row)}
          confirmLabel="Xóa"
          destructive
          disabled={actions.isDeleting(row)}
          onConfirm={() => actions.onDelete(row)}
        />
      </div>
    ),
  })

  return columns
}
