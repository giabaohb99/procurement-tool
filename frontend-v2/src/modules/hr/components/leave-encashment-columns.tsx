import type { DataTableColumn } from '@/shared/data-table'
import { formatDate } from '@/shared/utils/format-date'
import { formatEncashDays, isPayoutRejected, type LeaveEncashment } from '../types/leave-encashment'
import { LeaveStatusBadge } from './leave-status-badge'

/**
 * Cột của bảng Phiếu thanh toán nghỉ phép (duoc-CR-719). Tách khỏi trang danh sách cho trang gọn và cột test được.
 * `waitingIds` = id phiếu đang chờ CHÍNH tôi ký, để gắn chữ "Cần bạn duyệt" ở cột trạng thái.
 */
export function buildLeaveEncashmentColumns(waitingIds: Set<number>): DataTableColumn<LeaveEncashment>[] {
  return [
    {
      key: 'code',
      header: 'Số phiếu',
      width: 110,
      sortable: true,
      hideable: false,
      defaultPinned: true,
      cell: (r) => <span className="font-medium tabular-nums">{r.code}</span>,
    },
    {
      key: 'employee',
      //  Cột hiện tên kèm mã nhưng xếp theo họ tên — khóa gửi lên là `employee_name`.
      sortKey: 'employee_name',
      header: 'Người được thanh toán',
      width: 220,
      sortable: true,
      cell: (r) => (
        <span className="truncate">
          {r.employee_name || `#${r.employee_id}`}
          {r.employee_code && <span className="text-muted-foreground"> · {r.employee_code}</span>}
        </span>
      ),
    },
    {
      key: 'leave_type_name',
      header: 'Loại nghỉ',
      width: 140,
      sortable: true,
      cell: (r) => <span className="truncate">{r.leave_type_name || '—'}</span>,
    },
    {
      key: 'balance_year',
      header: 'Năm quỹ',
      width: 90,
      align: 'right',
      sortable: true,
      sortDescFirst: true,
      cell: (r) => <span className="tabular-nums">{r.balance_year}</span>,
    },
    {
      key: 'reason_kind',
      header: 'Lý do',
      width: 150,
      sortable: true,
      cell: (r) => <span className="truncate">{r.reason_kind_label}</span>,
    },
    {
      key: 'days',
      header: 'Số ngày',
      width: 90,
      align: 'right',
      sortable: true,
      sortDescFirst: true,
      cell: (r) => <span className="tabular-nums">{formatEncashDays(r.days)}</span>,
    },
    {
      key: 'status',
      header: 'Trạng thái',
      width: 190,
      sortable: true,
      cell: (r) => (
        <div className="flex min-w-0 items-center gap-1.5">
          <LeaveStatusBadge status={r.status} label={r.status_label} />
          {waitingIds.has(r.id) && (
            <span className="shrink-0 text-xs font-medium text-sky-700 dark:text-sky-300">Cần bạn duyệt</span>
          )}
        </div>
      ),
    },
    {
      key: 'payment_status',
      header: 'Trạng thái chi',
      width: 170,
      sortable: true,
      //  Đọc từ YCTT sinh ra khi duyệt — không lưu hai nơi. D7a: YCTT bị từ chối thì nói thẳng, không để chữ
      //  "Đã từ chối" trôi lẫn với trạng thái của chính phiếu.
      cell: (r) =>
        isPayoutRejected(r) ? (
          <span className="truncate font-medium text-amber-700 dark:text-amber-300">Kế toán từ chối chi</span>
        ) : r.payment_status ? (
          <span className="truncate">{r.payment_status_label}</span>
        ) : (
          <span className="text-muted-foreground">—</span>
        ),
    },
    {
      key: 'note',
      header: 'Ghi chú',
      width: 260,
      defaultHidden: true,
      sortable: true,
      cell: (r) => <span className="truncate">{r.note}</span>,
    },
    {
      key: 'created_at',
      header: 'Ngày tạo',
      width: 120,
      sortable: true,
      sortDescFirst: true,
      cell: (r) => <span className="tabular-nums">{formatDate(r.created_at)}</span>,
    },
  ]
}
