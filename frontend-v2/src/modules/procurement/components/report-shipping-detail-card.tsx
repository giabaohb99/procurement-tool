import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatPercent, formatQuantity } from '@/shared/utils/format-money'
import type { ShippingDetailRow } from '../types/purchase-report'

/**
 * Một DÒNG NHẬN HÀNG của bảng *Chi tiết theo đơn hàng* (tab Chi phí vận chuyển) ở khổ
 * điện thoại — thay cho bảng 11 cột ~1600px.
 *
 * ⚠️ **Đơn vị vận chuyển lên dòng đầu**: tab này hỏi "ai chở, tốn bao nhiêu" — bảng
 * khổ rộng cũng ghim đúng cột đó. Mã vật tư, tháng, MISA, số hóa đơn tụt xuống dòng phụ.
 *
 * ⚠️ **Hai số tiền đứng cạnh nhau kèm TỶ LỆ**: tỷ lệ = vận chuyển / giá trị đơn, bày
 * tách ra thì người đọc không thấy nó tính từ hai con số nào. Tiền in đủ chữ số.
 */
export function ReportShippingDetailCard({ row }: { row: ShippingDetailRow }) {
  const meta = [row.month, row.misa_code && `MISA ${row.misa_code}`].filter(Boolean)
  const receipt = [
    row.invoice_no && `HĐ ${row.invoice_no}`,
    row.received_date && `Nhận ${formatDate(row.received_date)}`,
  ].filter(Boolean)

  return (
    <div className="space-y-1.5">
      <p className="font-medium break-words text-foreground">{row.carrier || '—'}</p>

      <p className="flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
        <span className="font-medium text-sky-600 dark:text-sky-400">
          {row.product_code || '—'}
        </span>
        {meta.map((text) => (
          <span key={text}>
            <span aria-hidden="true">· </span>
            {text}
          </span>
        ))}
      </p>

      {receipt.length > 0 && (
        <p className="text-xs text-muted-foreground">{receipt.join(' · ')}</p>
      )}

      <p className="text-xs tabular-nums text-muted-foreground">
        SL đặt {formatQuantity(row.qty_order)} · nhận {formatQuantity(row.qty_received)}
      </p>

      <div className="grid grid-cols-[1fr_auto] gap-x-3 gap-y-0.5 text-xs">
        <span className="text-muted-foreground">Thành tiền đơn hàng</span>
        <span className="text-right tabular-nums">{formatMoney(row.order_amount)} đ</span>
        <span className="text-muted-foreground">Thành tiền vận chuyển</span>
        <span className="text-right text-sm font-semibold tabular-nums text-foreground">
          {formatMoney(row.ship_amount)} đ
        </span>
        <span className="text-muted-foreground">Tỷ lệ</span>
        <span className="text-right tabular-nums">{formatPercent(row.rate) || '—'}</span>
      </div>
    </div>
  )
}
