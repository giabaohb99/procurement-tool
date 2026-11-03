import type {
  LeaveBalanceMatrixColumn,
  LeaveBalanceMatrixRow,
} from '../api/leave-balance-matrix-api'
import { MatrixDayCell } from './leave-balance-matrix-day-cell'

/** Thẻ khổ hẹp: tên + mã + phòng, rồi từng loại nghỉ người đó CÓ quỹ, cuối cùng là tổng. */
export function LeaveBalanceMatrixCard({
  row,
  columns,
}: {
  row: LeaveBalanceMatrixRow
  columns: LeaveBalanceMatrixColumn[]
}) {
  const owned = columns.filter((c) => row.cells[String(c.leave_type_id)] !== undefined)
  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate font-medium">{row.name}</p>
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
