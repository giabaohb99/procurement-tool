import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import type { DailyRow } from '../types/purchase-report'

/**
 * Một NGÀY của hộp *Chi phí theo ngày* ở khổ điện thoại — thay cho bảng 4 cột tiền.
 *
 * ⚠️ **Vì sao bảng 4 cột vẫn phải đổi**: ba cột tiền in đủ chữ số ("123.456.789") mỗi
 * cột ~100px, cộng cột ngày là tràn khung ~340px của hộp thoại trên máy 390px — cột
 * Tổng (cột người ta đọc nhất) rơi ra ngoài mép phải. Thẻ để Tổng cùng hàng với ngày,
 * hai thành phần xuống dòng dưới; không rút gọn số kẻo lệch với tổng ở tiêu đề hộp.
 */
export function ReportDailyRowCard({ row }: { row: DailyRow }) {
  return (
    <div className="space-y-0.5 px-3 py-2.5">
      <p className="flex items-baseline justify-between gap-3">
        <span className="text-sm font-medium">{formatDate(row.date)}</span>
        <span className="text-sm font-semibold tabular-nums">{formatMoney(row.amount)} đ</span>
      </p>
      <p className="flex flex-wrap gap-x-3 text-xs tabular-nums text-muted-foreground">
        <span>Hàng hóa {formatMoney(row.goods)} đ</span>
        <span>Vận chuyển {formatMoney(row.shipping)} đ</span>
      </p>
    </div>
  )
}
