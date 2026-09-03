import type { DataTableColumn } from '@/shared/data-table'
import { formatDate } from '@/shared/utils/format-date'
import type { ApprovalFlowStrip as FlowStrip, LeaveRequest } from '../types/leave'
import { LeaveStatusCell } from './leave-status-cell'

/**
 * Các cột DÙNG CHUNG cho ba tab của màn Đơn nghỉ phép (CR-260).
 *
 * Ba tab đọc ba nguồn khác nhau (danh sách theo phạm vi · hàng đợi việc của tôi
 * · lịch sử tôi đã ký) nhưng tám cột giữa thì y hệt. Chép ba bản là ba lần phải
 * nhớ sửa khi thêm một cột, và chắc chắn có bản bị bỏ quên.
 *
 * ⚠️ Cột `key` phải KHÁC NHAU giữa các tab nếu ý nghĩa khác nhau: `DataTable`
 * nhớ độ rộng và trạng thái ẩn/hiện theo `storageKey` + `key`, nên hai cột trùng
 * khóa mà khác nội dung sẽ thừa hưởng độ rộng của nhau.
 */

export function codeColumn<T extends LeaveRequest>(): DataTableColumn<T> {
  return {
    key: 'code',
    header: 'Số đơn',
    cell: (r) => <span className="font-medium tabular-nums">{r.code}</span>,
    width: 110,
    hideable: false,
    defaultPinned: true,
  }
}

export function statusColumn<T extends LeaveRequest>(): DataTableColumn<T> {
  return {
    //  Trạng thái đứng NGAY SAU số đơn, không đẩy xuống cuối bảng: câu hỏi đầu
    //  tiên của người mở màn này là "đơn của tôi tới đâu rồi", mà cột cuối thì
    //  trôi tận mép phải màn 24".
    key: 'status',
    header: 'Trạng thái',
    cell: (r) => <LeaveStatusCell request={r} />,
    width: 230,
  }
}

/**
 * Cột LUỒNG DUYỆT — **chữ một dòng, không vẽ hình**.
 *
 * ⚠️ Từng dựng dạng dải chấm nối nhau (chặng đang chờ sáng lên) và đã BỎ ngày
 * 03/09/2026: trong một ô bảng cao 35px, năm cái vòng tròn nhỏ xếp ngang đọc ra
 * như một dãy biểu tượng lỗi chứ không ra một luồng, và cả cột nhìn nhiễu. Câu
 * chữ nói đúng thứ người ta cần biết — *đang ở chặng mấy, chờ ai* — mà không
 * chiếm chỗ và không có gì để xấu. Đừng dựng lại dải chấm.
 *
 * Câu này do BACKEND dựng (`steps_service._summary`), vì cùng câu đó còn dùng
 * cho bản in và thông báo — chép luật sang TypeScript là sớm muộn hai chỗ nói
 * khác nhau.
 *
 * `flowOf` tra luồng theo id đơn thay vì đọc thẳng từ dòng, vì ở tab «Đơn của
 * tôi» luồng đến từ một lượt gọi RIÊNG cho cả trang (`useLeaveFlowStrips`) —
 * gộp vào từng dòng nghĩa là mỗi dòng một lượt gọi mạng.
 */
export function flowColumn<T extends LeaveRequest>(
  flowOf: (row: T) => FlowStrip | null | undefined,
): DataTableColumn<T> {
  return {
    key: 'flow',
    header: 'Luồng duyệt',
    cell: (row) => {
      const flow = flowOf(row)
      if (!flow) return <span className="text-muted-foreground">Không qua luồng</span>
      return (
        //  `truncate` + `min-w-0`: câu tóm tắt mang tên người duyệt, mà tên
        //  người Việt dài — thiếu cặp này thì cột bị nong ra, đẩy vỡ cả bảng.
        <span className="block min-w-0 truncate" title={flow.summary}>
          {flow.summary}
        </span>
      )
    },
    width: 210,
  }
}

export function employeeColumn<T extends LeaveRequest>(): DataTableColumn<T> {
  return {
    key: 'employee_name',
    header: 'Người nghỉ',
    cell: (r) => r.employee_name || `#${r.employee_id}`,
    width: 170,
  }
}

export function leaveTypeColumn<T extends LeaveRequest>(): DataTableColumn<T> {
  return {
    key: 'leave_type_name',
    header: 'Loại nghỉ',
    cell: (r) => r.leave_type_name || '—',
    width: 130,
  }
}

export function dateColumns<T extends LeaveRequest>(): DataTableColumn<T>[] {
  return [
    {
      key: 'from_date',
      header: 'Từ ngày',
      cell: (r) => <span className="tabular-nums">{formatDate(r.from_date)}</span>,
      width: 110,
      sortable: true,
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
    },
  ]
}

export function reasonColumn<T extends LeaveRequest>(): DataTableColumn<T> {
  return {
    key: 'reason',
    header: 'Lý do',
    cell: (r) => r.reason,
    //  ⚠️ Đừng khai `compactHidden` ở đây — thuộc tính đó chỉ có nghĩa với
    //  `LinesTable` (bảng dòng chứng từ). `DataTable` không đọc nó, nên đặt vào
    //  chỉ tạo ảo giác là cột đã được giấu bớt.
    wrap: true,
    minWidth: 180,
  }
}
