import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { formatDate } from '@/shared/utils/format-date'
import { useLeaveRequests } from '../hooks/use-leave'
import type { LeaveBalance, LeaveRequest } from '../types/leave'
import { LeaveStatusCell } from './leave-status-cell'

interface LeaveBalanceRequestsCardProps {
  balance: LeaveBalance
}

//  Đủ để nhìn hết một năm của một người. Quá số này thì họ đã nghỉ nhiều hơn cả
//  hạn mức, và lúc đó chuyện cần xem là quỹ chứ không phải danh sách đơn.
const MAX_ROWS = 100

/**
 * ĐƠN NGHỈ của chính người này, đúng loại nghỉ và đúng năm của dòng quỹ.
 *
 * ⚠️ Đây là thứ trả lời câu hỏi mà con số không trả lời được: *"đã nghỉ 3 ngày"
 * — nghỉ hôm nào, vì việc gì, ai duyệt.* Không có nó thì người định điều chỉnh
 * quỹ phải mở tab khác, lọc lại theo tên và loại nghỉ, rồi quay về đây gõ số —
 * và đúng lúc quay về thì không còn nhớ mình vừa đọc gì.
 *
 * Lọc theo khoảng ngày của NĂM chứ không có ô `year`: backend lọc theo GIAO
 * NHAU của khoảng nghỉ, nên một đơn nghỉ vắt từ 28/12 sang 03/01 lọt vào cả hai
 * năm — đúng ý, vì nó thật sự tiêu quỹ của cả hai.
 */
export function LeaveBalanceRequestsCard({ balance }: LeaveBalanceRequestsCardProps) {
  const navigate = useNavigate()

  const { data, isLoading, isError } = useLeaveRequests({
    page: 1,
    page_size: MAX_ROWS,
    employee_id: String(balance.employee_id),
    leave_type_id: String(balance.leave_type_id),
    from_date: `${balance.year}-01-01`,
    to_date: `${balance.year}-12-31`,
  })

  const columns = useMemo<DataTableColumn<LeaveRequest>[]>(
    () => [
      {
        key: 'code',
        header: 'Số đơn',
        cell: (r) => <span className="font-medium tabular-nums">{r.code}</span>,
        width: 110,
        hideable: false,
      },
      {
        key: 'status',
        header: 'Trạng thái',
        cell: (r) => <LeaveStatusCell request={r} />,
        width: 230,
      },
      {
        key: 'from_date',
        header: 'Từ ngày',
        cell: (r) => <span className="tabular-nums">{formatDate(r.from_date)}</span>,
        width: 110,
      },
      {
        key: 'to_date',
        header: 'Đến ngày',
        cell: (r) => <span className="tabular-nums">{formatDate(r.to_date)}</span>,
        width: 110,
      },
      {
        key: 'total_days',
        header: 'Số ngày',
        cell: (r) => <span className="font-medium tabular-nums">{r.total_days}</span>,
        width: 90,
        align: 'right',
      },
      {
        key: 'reason',
        header: 'Lý do',
        cell: (r) => r.reason,
        wrap: true,
        minWidth: 180,
      },
    ],
    [],
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Đơn nghỉ trong năm {balance.year}</CardTitle>
        <p className="text-sm text-muted-foreground">
          Chỉ những đơn thuộc loại nghỉ này. Đơn đã hủy hay bị từ chối không trừ quỹ.
        </p>
      </CardHeader>

      <CardContent>
        <DataTable
          columns={columns}
          rows={data?.items}
          getRowId={(r) => r.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Người này chưa nộp đơn nghỉ nào thuộc loại nghỉ này trong năm."
          storageKey="hr.leave-balance-requests"
          onRowClick={(r) => navigate(appRoutes.hr.leaveRequestDetail(r.id))}
        />
      </CardContent>
    </Card>
  )
}
