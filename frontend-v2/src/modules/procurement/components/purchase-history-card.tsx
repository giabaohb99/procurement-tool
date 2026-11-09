import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import type { PurchaseHistoryRow } from '../api/purchase-request-support-api'

interface PurchaseHistoryCardProps {
  row: PurchaseHistoryRow
  /** Chứng từ đang khóa sửa: chỉ xem giá cũ, không có nút điền giá. */
  readOnly: boolean
  onPick: () => void
}

/**
 * Một LẦN MUA cũ ở khổ điện thoại — thay cho bảng 11 cột (`min-w-[940px]`) của hộp
 * *Lịch sử mua hàng gần nhất*.
 *
 * ⚠️ **NCC lên dòng đầu**: hộp này mở ra để SO GIÁ GIỮA CÁC NCC cho cùng một mã hàng,
 * nên thứ phân biệt các lần mua là ai bán; mã PO tụt xuống dòng phụ.
 *
 * ⚠️ **Đơn giá đứng trước, to nhất** — đó là con số người ta mở hộp để tìm; thành tiền
 * còn tùy số lượng của lần mua đó nên chỉ để đối chiếu.
 *
 * ⚠️ **Số tiền in TRƠN, không gắn "đ"** — giống hệt bảng khổ rộng. `price` / `amount` chép
 * thẳng từ dòng ĐMH, mà ĐMH nhập khẩu lưu NGUYÊN TỆ: gắn "đ" là 2,8 USD/kg đọc thành
 * "2,8 đ/kg". Dòng lịch sử không mang mã tiền tệ nên thẻ không được đoán.
 *
 * ⚠️ **Chọn bằng nút "Dùng giá này", không bằng chạm cả thẻ**: ở bảng bấm cả dòng là
 * điền giá, nhưng trên máy cảm ứng người ta chạm vào thẻ để đọc cho rõ — chạm nhầm là
 * hộp đóng và giá trong phiếu đã bị thay. Nút là ANH EM của khối chữ.
 */
export function PurchaseHistoryCard({ row, readOnly, onPick }: PurchaseHistoryCardProps) {
  const meta = [formatDate(row.order_date) || row.order_date, row.company_name].filter(Boolean)

  return (
    <div className="space-y-1.5 p-3">
      <p className="font-medium break-words text-foreground">
        {row.supplier_name || row.supplier_code || '—'}
      </p>

      <p className="flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
        {row.po_code ? (
          <span className="font-medium text-sky-600 dark:text-sky-400">{row.po_code}</span>
        ) : (
          <span>Dữ liệu cũ</span>
        )}
        {meta.map((text) => (
          <span key={text}>
            <span aria-hidden="true">· </span>
            {text}
          </span>
        ))}
      </p>

      {row.invoice_name && (
        //  bao-CR-522: tên lấy từ danh mục (dòng cũ) thì in nghiêng mờ, cùng luật với bảng.
        <p
          className={cn(
            'text-xs break-words',
            row.invoice_name_from_catalog && 'text-muted-foreground italic',
          )}
          title={
            row.invoice_name_from_catalog
              ? 'Dữ liệu cũ không có — lấy theo danh mục sản phẩm'
              : undefined
          }
        >
          <span className="text-muted-foreground not-italic">Tên HĐ </span>
          {row.invoice_name}
        </p>
      )}

      <p className="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-xs text-muted-foreground">
        <span className="text-sm font-semibold tabular-nums text-foreground">
          {formatUnitPrice(row.price)}
          {row.unit ? `/${row.unit}` : ''}
        </span>
        <span className="tabular-nums">SL {formatQuantity(row.qty_order)}</span>
        <span className="tabular-nums">VAT {formatQuantity(row.vat)}%</span>
      </p>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs text-muted-foreground">
          Thành tiền{' '}
          <span className="font-medium tabular-nums text-foreground">
            {formatMoney(row.amount)}
          </span>
        </span>
        {!readOnly && (
          <Button type="button" variant="outline" size="sm" onClick={onPick}>
            Dùng giá này
          </Button>
        )}
      </div>
    </div>
  )
}
