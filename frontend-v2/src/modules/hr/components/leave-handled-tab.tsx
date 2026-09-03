import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useLeaveHandled } from '../hooks/use-leave'
import type { LeaveInboxRow } from '../types/leave'
import {
  codeColumn,
  dateColumns,
  employeeColumn,
  flowColumn,
  leaveTypeColumn,
  statusColumn,
} from './leave-request-columns'

/**
 * Tab «TÔI ĐÃ DUYỆT» — nhìn lại những đơn chính tôi vừa quyết định (CR-260).
 *
 * ⚠️ Đây là màn *"nhớ lại hôm qua mình ký cái gì"*, **không phải sổ tra cứu**:
 * backend chặn ở 30 ngày gần nhất và không phân trang. Muốn tra đủ lịch sử thì
 * mở dấu vết của chính tờ đơn, nơi có cả những người khác đã làm gì.
 *
 * ⚠️ **Không dựng cột «Tôi đã» và «Lúc»** (bỏ 03/09/2026). Mọi dòng trong tab
 * này đều do chính người đang xem quyết, nên hai cột đó chỉ lặp lại cái tên của
 * tab và một mốc giờ mà không ai dùng để làm gì — trong khi chúng chiếm 260px
 * đầu bảng, đẩy những cột thật sự phân biệt các dòng (ai nghỉ, ngày nào) trôi
 * sang phải. Giờ ký chính xác vẫn còn ở dấu vết trong trang chi tiết.
 */
export function LeaveHandledTab() {
  const navigate = useNavigate()
  const { data, isLoading, isError } = useLeaveHandled()

  const columns = useMemo<DataTableColumn<LeaveInboxRow>[]>(
    () => [
      codeColumn(),
      statusColumn(),
      flowColumn((row) => row.flow),
      employeeColumn(),
      leaveTypeColumn(),
      ...dateColumns(),
    ],
    [],
  )

  return (
    <DataTable
      fillHeight
      columns={columns}
      rows={data?.items}
      getRowId={(r) => r.id}
      isLoading={isLoading}
      isError={isError}
      emptyMessage="Bạn chưa duyệt đơn nghỉ phép nào trong 30 ngày qua."
      storageKey="hr.leave-handled"
      onRowClick={(r) => navigate(appRoutes.hr.leaveRequestDetail(r.id))}
    />
  )
}
