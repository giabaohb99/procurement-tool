import { ColumnChart } from '@/shared/ui/column-chart'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { useDailyReport } from '../hooks/use-purchase-report'
import { shortMoney } from '../types/purchase-report'

interface ReportDailyDialogProps {
  /** `'YYYY-MM'` — rỗng thì hộp thoại đóng và KHÔNG gọi API. */
  month: string
  /** Nhãn tháng hiện trên tiêu đề, vd "08/2026". */
  monthLabel: string
  companyId?: string
  onClose: () => void
}

/**
 * Chi phí theo NGÀY của một tháng — mở ra khi bấm vào cột trên biểu đồ "Chi phí
 * mua theo tháng".
 *
 * Cùng nguồn số với biểu đồ tháng (công nợ phát sinh theo ngày nhận hàng), chỉ
 * khác độ mịn, nên tổng ở đây phải khớp đúng chiều cao cột vừa bấm.
 */
export function ReportDailyDialog({
  month,
  monthLabel,
  companyId,
  onClose,
}: ReportDailyDialogProps) {
  const { data, isLoading } = useDailyReport(month, companyId)
  const days = data?.days ?? []

  return (
    <Dialog open={!!month} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[88vh] gap-4 overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Chi phí theo ngày — {monthLabel}</DialogTitle>
          <DialogDescription>
            {isLoading ? 'Đang tải…' : `Tổng ${formatMoney(data?.total ?? 0)} đ`}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <p className="py-10 text-center text-sm text-muted-foreground">Đang tải…</p>
        ) : days.length === 0 ? (
          <p className="py-10 text-center text-sm text-muted-foreground">
            Không có phát sinh trong tháng này.
          </p>
        ) : (
          <>
            <ColumnChart
              data={days.map((row) => ({ label: row.day, value: row.amount }))}
              height={220}
              unit="đ"
              formatValue={shortMoney}
            />

            <Table>
              <TableHeader className="bg-muted">
                <TableRow className="hover:bg-muted">
                  <TableHead>Ngày</TableHead>
                  <TableHead className="text-right">Hàng hóa</TableHead>
                  <TableHead className="text-right">Vận chuyển</TableHead>
                  <TableHead className="text-right">Tổng</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {days.map((row) => (
                  <TableRow key={row.date}>
                    <TableCell>{formatDate(row.date)}</TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatMoney(row.goods)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatMoney(row.shipping)}
                    </TableCell>
                    <TableCell className="text-right font-semibold tabular-nums">
                      {formatMoney(row.amount)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
