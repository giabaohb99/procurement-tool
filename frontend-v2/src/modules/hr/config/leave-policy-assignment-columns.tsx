import type { ReactNode } from 'react'

import type { DataTableColumn } from '@/shared/data-table'
import { formatDate } from '@/shared/utils/format-date'
import { LeavePolicyAssignmentStateBadge } from '../components/leave-policy-assignment-state-badge'
import { LeavePolicyCurrentYearQuotas } from '../components/leave-policy-current-year-quotas'
import type { LeavePolicyAssignment } from '../types/leave-policy'

/**
 * Cột của bảng PHÂN BỔ CHÍNH SÁCH (duoc-CR-717) — dùng chung cho màn danh sách phân bổ và tab
 * "Đang phân bổ" trong chi tiết chính sách, để hai nơi nói cùng một câu.
 */
interface AssignmentColumnOptions {
  /** Ẩn cột "Chính sách" ở tab của chính chính sách đó (cột nào cũng cùng một tên). */
  showPolicy: boolean
  /** Ô hành động cuối dòng (Kết thúc · Xóa) — chỉ màn danh sách có. */
  renderActions?: (row: LeavePolicyAssignment) => ReactNode
}

export function buildLeavePolicyAssignmentColumns({
  showPolicy,
  renderActions,
}: AssignmentColumnOptions): DataTableColumn<LeavePolicyAssignment>[] {
  const columns: DataTableColumn<LeavePolicyAssignment>[] = [
    {
      key: 'employee',
      header: 'Nhân sự',
      width: 240,
      hideable: false,
      //  duoc-CR-748: xếp theo HỌ TÊN (ô hiện tên kèm mã), không theo id nhân sự.
      sortable: true,
      sortKey: 'employee_name',
      cell: (a) => (
        <span className="min-w-0">
          <span className="font-medium">{a.employee_name || `#${a.employee_id}`}</span>
          {a.employee_code && <span className="text-muted-foreground"> · {a.employee_code}</span>}
        </span>
      ),
    },
  ]
  if (showPolicy) {
    columns.push({
      key: 'policy',
      header: 'Chính sách',
      width: 220,
      sortable: true,
      sortKey: 'policy_name',
      cell: (a) => a.policy_name || `#${a.policy_id}`,
    })
  }
  columns.push(
    {
      key: 'effective_from',
      header: 'Từ ngày',
      width: 120,
      sortable: true,
      cell: (a) => <span className="tabular-nums">{formatDate(a.effective_from)}</span>,
    },
    {
      key: 'effective_to',
      header: 'Đến ngày',
      width: 140,
      //  "Không thời hạn" là ô trống nên luôn xuống CUỐI cả hai chiều (luật chung của bảng, không coi là vô hạn).
      sortable: true,
      cell: (a) =>
        a.effective_to ? (
          <span className="tabular-nums">{formatDate(a.effective_to)}</span>
        ) : (
          <span className="text-muted-foreground">Không thời hạn</span>
        ),
    },
    {
      key: 'state',
      header: 'Trạng thái',
      width: 140,
      //  Dòng đời Sắp tới → Đang hiệu lực → Đã kết thúc, dẫn xuất theo ngày hôm nay (giờ VN) ở backend.
      sortable: true,
      sortKey: 'state',
      cell: (a) => <LeavePolicyAssignmentStateBadge state={a.state} />,
    },
    {
      //  Cột "Hạn mức năm nay" cố ý KHÔNG xếp được: số lấy từ bảng quỹ phép ở truy vấn khác, không có biểu thức SQL khớp.
      //  duoc-CR-745: kiểu mục Leaves của ERPNext — quỹ năm nay mà phân bổ này quyết định, bấm sang dòng quỹ.
      key: 'current_year_quotas',
      header: 'Hạn mức năm nay',
      width: 190,
      cell: (a) => <LeavePolicyCurrentYearQuotas quotas={a.current_year_quotas} />,
    },
    {
      key: 'note',
      header: 'Ghi chú',
      width: 260,
      sortable: true,
      cell: (a) => a.note,
    },
  )
  if (renderActions) {
    columns.push({
      key: 'actions',
      header: 'Thao tác',
      width: 190,
      hideable: false,
      cell: (a) => (
        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          {renderActions(a)}
        </div>
      ),
    })
  }
  return columns
}
