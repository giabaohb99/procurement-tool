import type {
  LeaveBalanceMatrixColumn,
  LeaveBalanceMatrixRow,
} from '../api/leave-balance-matrix-api'
import { pickAccrualInfo } from '../utils/leave-accrual-status'
import { LeaveAccrualStatusBadge } from './leave-accrual-status-badge'
import { MatrixDayCell } from './leave-balance-matrix-day-cell'

/** Thẻ khổ hẹp: tên + mã + phòng, rồi từng loại nghỉ người đó CÓ quỹ, cuối cùng là tổng. */
export function LeaveBalanceMatrixCard({
  row,
  columns,
  hideNoContract = false,
}: {
  row: LeaveBalanceMatrixRow
  columns: LeaveBalanceMatrixColumn[]
  /** Ẩn nhãn *Chưa có HĐLĐ* (duoc-CR-762 phương án B). */
  hideNoContract?: boolean
}) {
  const owned = columns.filter((c) => row.cells[String(c.leave_type_id)] !== undefined)
  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between gap-3">
        <div className="min-w-0">
          <div className="flex min-w-0 items-center gap-1.5">
            <p className="truncate font-medium">{row.name}</p>
            <LeaveAccrualStatusBadge
              info={pickAccrualInfo(Object.values(row.accrual ?? {}), hideNoContract)}
              hideContractWarning={hideNoContract}
            />
          </div>
          <p className="truncate text-xs text-muted-foreground">
            {row.code}
            {row.department_name ? ` · ${row.department_name}` : ''}
          </p>
        </div>
        <span className="shrink-0 text-sm">
          Tổng <MatrixDayCell value={row.total} strong />
        </span>
      </div>
      {owned.length > 0 ? (
        <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
          {owned.map((c) => (
            <div key={c.leave_type_id} className="flex justify-between gap-2">
              <dt className="truncate text-muted-foreground">{c.name}</dt>
              <dd>
                <MatrixDayCell value={row.cells[String(c.leave_type_id)]} />
              </dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="text-xs text-muted-foreground">Chưa có dòng quỹ nào trong năm này.</p>
      )}
    </div>
  )
}
