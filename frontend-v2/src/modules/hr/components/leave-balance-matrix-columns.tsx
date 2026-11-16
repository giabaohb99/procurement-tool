import type { DataTableColumn } from '@/shared/data-table'
import type {
  LeaveBalanceMatrixColumn,
  LeaveBalanceMatrixRow,
} from '../api/leave-balance-matrix-api'
import { pickAccrualInfo } from '../utils/leave-accrual-status'
import { AccrualStartTooltip, LeaveAccrualStatusBadge } from './leave-accrual-status-badge'
import { PolicyName } from './leave-balance-cells'
import { MatrixDayCell } from './leave-balance-matrix-day-cell'

/**
 * Bộ cột của ma trận: Mã NV · Họ tên · Phòng ban · Chính sách · một cột mỗi loại nghỉ (theo `columns` backend
 * trả, ĐỦ cho cả kết quả chứ không riêng trang đang xem) · Tổng còn lại.
 *
 * Chỉ ba cột đầu (Mã NV, Họ tên, Phòng ban) xếp được (duoc-CR-748). Cột Chính sách, từng loại nghỉ và Tổng cố ý
 * KHÔNG xếp: số ngày dùng được do backend tính bằng Python trên trang đang xem, không có biểu thức SQL khớp.
 */
export function buildLeaveBalanceMatrixColumns(
  columns: LeaveBalanceMatrixColumn[],
  /** Ẩn biểu tượng *Chưa có HĐLĐ* — quá nửa số người trên trang thiếu (duoc-CR-762 phương án B). */
  hideNoContract = false,
): DataTableColumn<LeaveBalanceMatrixRow>[] {
  return [
    { key: 'code', header: 'Mã NV', width: 100, defaultPinned: true, sortable: true, cell: (r) => r.code },
    {
      key: 'name',
      header: 'Họ tên',
      width: 200,
      hideable: false,
      defaultPinned: true,
      sortable: true,
      //  duoc-CR-762: nhãn thử việc / chưa có HĐLĐ đứng cạnh TÊN (cột loại nghỉ chỉ 120px), dạng BIỂU TƯỢNG + gợi ý rê
      //  chuột — nhãn chữ đầy đủ cắt tên còn ba chữ cái.
      cell: (r) => (
        <span className="flex min-w-0 items-center gap-1.5">
          <span className="truncate font-medium">{r.name}</span>
          <LeaveAccrualStatusBadge
            compact
            info={pickAccrualInfo(Object.values(r.accrual ?? {}), hideNoContract)}
            hideContractWarning={hideNoContract}
          />
        </span>
      ),
    },
    {
      key: 'department',
      header: 'Phòng ban',
      width: 170,
      //  Xếp theo TÊN phòng ban; "Chưa gắn" là ô trống nên luôn xuống cuối (duoc-CR-748).
      sortable: true,
      sortKey: 'department_name',
      cell: (r) => r.department_name || <span className="text-muted-foreground">Chưa gắn</span>,
    },
    {
      //  duoc-CR-745: chính sách nào đang quyết định hạn mức — nối sang tab Phân bổ của màn Chính sách nghỉ phép.
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
      //  Người đang tích (duoc-CR-762): rê chuột vào ô ra *Tích từ dd/mm/yyyy*, không thêm chữ nào.
      cell: (r) => (
        <AccrualStartTooltip info={r.accrual?.[String(c.leave_type_id)]}>
          {/*  Bọc `span` DOM: `asChild` cần phần tử nhận được ref + sự kiện, `MatrixDayCell` không chuyển tiếp. */}
          <span>
            <MatrixDayCell value={r.cells[String(c.leave_type_id)]} />
          </span>
        </AccrualStartTooltip>
      ),
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
