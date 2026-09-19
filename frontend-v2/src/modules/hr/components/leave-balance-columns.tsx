import type { DataTableColumn } from '@/shared/data-table'
import { cn } from '@/shared/utils/cn'
import {
  rowHasRealQuota,
  rowTotals,
  type LeaveBalanceRow,
} from '../utils/group-leave-balances'
import { DayCount, NameCell } from './leave-balance-cells'

/**
 * Cột của bảng QUỸ PHÉP NĂM — bảng gom theo NGƯỜI, loại nghỉ là dòng con.
 *
 * ⚠️ **Năm cột bày sẵn, sáu cột ẩn sẵn.** Bản cũ bày cả mười một cột: ở màn
 * 1600px nó vẫn tràn, và thứ tràn ra ngoài mép phải lại đúng là cột «Còn lại» —
 * con số duy nhất người ta mở màn này để xem. Sáu cột giải thích (hạn mức gốc,
 * thâm niên, chuyển năm trước, đã chuyển đi, hết hạn, điều chỉnh tay) gần như
 * luôn bằng 0 nên chúng chiếm 750px để bày ra một biển dấu gạch; ai cần thì bật
 * lại ở menu «Cột», mà phép tính đầy đủ thì trang chi tiết đã bày sẵn rồi.
 *
 * Ô định danh và ô số ngày nằm ở `leave-balance-cells.tsx` — tách ra để tệp này
 * chỉ còn khai báo cột, và để `react-refresh` không cằn nhằn một tệp vừa xuất
 * component vừa xuất hàm dựng.
 */
interface BuildOptions {
  /** Id nhân sự của những nhóm đang bung. */
  expanded: ReadonlySet<number>
  onToggle: (employeeId: number) => void
}

export function buildLeaveBalanceColumns({
  expanded,
  onToggle,
}: BuildOptions): DataTableColumn<LeaveBalanceRow>[] {
  return [
    {
      key: 'employee_name',
      header: 'Nhân sự',
      cell: (row) => <NameCell row={row} expanded={expanded} onToggle={onToggle} />,
      //  ⚠️ CỐ Ý không khai `width`: cột này nuốt trọn chỗ thừa (xem
      //  `DataTableColumn.width`). Khai số cứng thì khi chỉ còn năm cột bày sẵn,
      //  phần dư được chia ĐỀU cho cả năm — mỗi cột số phình lên gần 190px và
      //  con số nằm nép mép phải, cách tiêu đề của chính nó cả một gang tay.
      minWidth: 240,
      hideable: false,
      defaultPinned: true,
    },
    {
      key: 'total_days',
      header: 'Tổng cấp',
      //  Thay cho cột «Hạn mức» cũ ở vị trí bày sẵn: ở hàng NHÓM thì hạn mức
      //  gốc cộng lại không còn nghĩa (cộng hạn mức phép năm với hạn mức nghỉ
      //  cưới ra một con số không ai dùng), còn `total_days` là "tổng được
      //  nghỉ" — đúng vế trái của phép tính mà cột «Còn lại» là kết quả.
      cell: (row) => <DayCount value={rowTotals(row).total_days} />,
      width: 110,
      align: 'right',
    },
    {
      key: 'allocated_days',
      header: 'Hạn mức',
      cell: (row) => <DayCount value={rowTotals(row).allocated_days} />,
      width: 110,
      align: 'right',
      defaultHidden: true,
    },
    {
      key: 'seniority_days',
      header: 'Thâm niên',
      cell: (row) => <DayCount value={rowTotals(row).seniority_days} signed />,
      width: 110,
      align: 'right',
      defaultHidden: true,
    },
    {
      key: 'carried_days',
      header: 'Chuyển năm trước',
      cell: (row) => <DayCount value={rowTotals(row).carried_days} signed />,
      width: 150,
      align: 'right',
      defaultHidden: true,
    },
    {
      key: 'carried_out_days',
      header: 'Đã chuyển đi',
      //  Phần đã mang sang năm sau lúc kết sổ. Nó ĐÃ bị trừ khỏi «Còn lại»,
      //  nên không có cột này thì số dư năm cũ tụt mà không dòng nào giải
      //  thích — và người xem sẽ đi tìm xem ai vừa nghỉ mấy ngày đó.
      cell: (row) => <DayCount value={rowTotals(row).carried_out_days} />,
      width: 130,
      align: 'right',
      defaultHidden: true,
    },
    {
      key: 'carried_expired_days',
      header: 'Hết hạn',
      //  Phép mang sang quá hạn dùng thì mất. Cột này KHÔNG nằm trong công
      //  thức còn lại — nó chỉ nói ra chỗ số ngày đã đi đâu.
      cell: (row) => (
        <DayCount
          value={rowTotals(row).carried_expired_days}
          className="text-muted-foreground line-through"
        />
      ),
      width: 110,
      align: 'right',
      defaultHidden: true,
    },
    {
      key: 'adjusted_days',
      header: 'Điều chỉnh tay',
      //  Cột DUY NHẤT mang được số âm — `signed` tự xử dấu, gắn `+` cứng ở
      //  đây sẽ ra "+-2".
      cell: (row) => <DayCount value={rowTotals(row).adjusted_days} signed />,
      width: 140,
      align: 'right',
      defaultHidden: true,
    },
    {
      key: 'used_days',
      header: 'Đã nghỉ',
      cell: (row) => <DayCount value={rowTotals(row).used_days} />,
      width: 110,
      align: 'right',
    },
    {
      key: 'pending_days',
      header: 'Chờ duyệt',
      //  Hổ phách vì đây là ngày ĐANG GIỮ CHỖ: chưa nghỉ nhưng cũng không
      //  tiêu được nữa. Số 0 vẫn để mờ như mọi cột khác — tô cả cột vàng khè
      //  trong khi chẳng có gì đang chờ là màu mất hết nghĩa.
      cell: (row) => (
        <DayCount
          value={rowTotals(row).pending_days}
          className="text-amber-600 dark:text-amber-400"
        />
      ),
      width: 110,
      align: 'right',
    },
    {
      key: 'remaining_days',
      header: 'Còn lại',
      //  ⚠️ KHÔNG `text-primary`: primary là navy — đúng màu nút hành động
      //  chính — nên con số đọc ra như một cái link bấm được. Đây là cột người
      //  ta quét mắt tìm, đậm hơn là đủ. Hết phép thì tô đỏ, vì đó là thứ Nhân
      //  sự cần thấy ngay giữa một bảng toàn số.
      //
      //  ⚠️ Nhưng chỉ đỏ khi CÓ QUỸ mà tiêu hết. Loại nghỉ không cấp hạn mức
      //  (tang chế, cưới hỏi, nghỉ bù…) luôn còn 0 và chiếm phần lớn số dòng —
      //  tô đỏ hết thì màu đỏ mất nghĩa đúng chỗ nó cần có nghĩa.
      cell: (row) => {
        const value = rowTotals(row).remaining_days
        return (
          <DayCount
            value={value}
            alwaysShow
            className={cn(
              'font-semibold',
              value > 0
                ? 'text-foreground'
                : rowHasRealQuota(row)
                  ? 'text-destructive'
                  : 'text-muted-foreground',
            )}
          />
        )
      },
      width: 110,
      align: 'right',
      hideable: false,
    },
  ]
}
