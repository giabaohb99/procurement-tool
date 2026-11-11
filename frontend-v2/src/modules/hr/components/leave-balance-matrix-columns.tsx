import type { DataTableColumn } from '@/shared/data-table'
import type {
  LeaveBalanceMatrixColumn,
  LeaveBalanceMatrixRow,
} from '../api/leave-balance-matrix-api'
import { PolicyName } from './leave-balance-cells'
import { MatrixDayCell } from './leave-balance-matrix-day-cell'

/**
 * Bộ cột của ma trận: Mã NV · Họ tên · Phòng ban · Chính sách · một cột mỗi loại nghỉ (theo `columns` backend
 * trả, ĐỦ cho cả kết quả chứ không riêng trang đang xem) · Tổng còn lại.
 */
export function buildLeaveBalanceMatrixColumns(
  columns: LeaveBalanceMatrixColumn[],
): DataTableColumn<LeaveBalanceMatrixRow>[] {
  return [
    { key: 'code', header: 'Mã NV', width: 100, defaultPinned: true, cell: (r) => r.code },
    {
      key: 'name',
      header: 'Họ tên',
      width: 200,
      hideable: false,
      defaultPinned: true,
      cell: (r) => <span className="font-medium">{r.name}</span>,
    },
    {
      key: 'department',
      header: 'Phòng ban',
      width: 170,
      cell: (r) => r.department_name || <span className="text-muted-foreground">Chưa gắn</span>,
    },
    {
      //  duoc-CR-745: chính sách nào đang quyết định hạn mức — nối sang màn Phân bổ chính sách.
      key: 'policy',
      header: 'Chính sách',
      width: 190,
      cell: (r) => <PolicyName name={r.policy_name} />,
    },
    ...columns.map<DataTableColumn<LeaveBalanceMatrixRow>>((c) => ({
      //  Tiền tố `lt-` để khóa cột loại nghỉ không đụng `code` / `name` / `total`.
      key: `lt-${c.leave_type_id}`,
      header: c.name,
      width: 120,
      align: 'right',
      //  ⚠️ Khóa `cells` là CHUỖI id — đọc bằng số là ra `undefined` hết, cả bảng thành "—".
      cell: (r) => <MatrixDayCell value={r.cells[String(c.leave_type_id)]} />,
    })),
    {
      key: 'total',
      header: 'Tổng còn lại',
      width: 120,
      align: 'right',
      hideable: false,
      //  Review L8: luôn là cột CUỐI, kể cả khi người dùng đã lưu bố cục cột — cột loại nghỉ mới mọc thêm
      //  (backend thêm loại) nối vào cuối thứ tự đã lưu và đẩy "Tổng" vào giữa bảng nếu không ghim.
      stickyRight: true,
      cell: (r) => <MatrixDayCell value={r.total} strong />,
    },
  ]
}
