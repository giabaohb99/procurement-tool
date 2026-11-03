import type { ReactNode } from 'react'

import type { DataTableColumn } from '@/shared/data-table'
import { formatDate } from '@/shared/utils/format-date'
import { LeavePolicyAssignmentStateBadge } from '../components/leave-policy-assignment-state-badge'
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
      cell: (a) => a.policy_name || `#${a.policy_id}`,
    })
  }
  columns.push(
    {
      key: 'effective_from',
      header: 'Từ ngày',
      width: 120,
      cell: (a) => <span className="tabular-nums">{formatDate(a.effective_from)}</span>,
    },
    {
      key: 'effective_to',
      header: 'Đến ngày',
      width: 140,
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
      cell: (a) => <LeavePolicyAssignmentStateBadge state={a.state} />,
    },
    {
      key: 'note',
      header: 'Ghi chú',
      width: 260,
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
