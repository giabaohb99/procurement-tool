import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { PayableAgingBadge, PayableStatusBadge } from './payable-badges'
import { PAYABLE_SOURCE_LABELS, type Payable } from '../types/payable'

/**
 * Một KHOẢN CÔNG NỢ ở khổ điện thoại — xem `DataTableProps.mobileCard`.
 *
 * Bảng khai **15 cột** (17 khi đủ quyền tick chọn + cấn trừ), bề rộng tự nhiên
 * ~2200px trong khung ~322px: phần nhìn thấy được là *Nhà cung cấp* cộng một
 * mẩu *Mã NCC*, còn **hạn trả, tuổi nợ và SỐ CÒN LẠI** — ba thứ quyết định có
 * đi đòi chứng từ để lên đề nghị chi hay không — thì nằm ngoài mép phải.
 *
 * ⚠️ **Tên NCC KHÔNG cắt cụt** (không `truncate`), khác `PaymentRequestCard`.
 * Đây là sổ để ĐỐI CHIẾU: khách báo 31/08/2026 rằng tên bị cắt thành "Công ty
 * TNHH Thương mại…" thì phải rê chuột từng dòng mới đọc nổi — cùng lý do cột
 * `supplier_name` của bảng khai `wrap: true`. Thà thẻ cao thêm một dòng.
 *
 * ⚠️ **Loại nợ (Hàng hóa / Vận chuyển) phải có mặt.** Một đơn mua hàng sinh ra
 * HAI dòng nợ — một cho hàng, một cho cước — cùng NCC, cùng mã ĐMH. Bỏ trường
 * này thì hai thẻ liền nhau giống hệt nhau và không cách nào biết thẻ nào là
 * thẻ nào.
 *
 * ⚠️ **Số tiền KHÔNG rút gọn** và luôn hiện «Còn lại» chứ không hiện tổng nợ:
 * tổng nợ là con số đã trả một phần, còn thứ người ta vào đây để biết là còn
 * phải chi bao nhiêu. Trả một phần thì bày thêm phần ĐÃ TRẢ, nếu không «Còn
 * lại» nhỏ hơn tổng mà không có gì giải thích vì sao.
 *
 * ⚠️ **Không nút nào trong thẻ**: `DataTableMobileCards` bọc cả thẻ trong một
 * `<button>` (bảng này có `onRowClick` mở ĐMH), lồng nút vào trong nút là HTML
 * sai và trên máy cảm ứng hai vùng chạm đè nhau. Ô tick chọn và nút cấn trừ vì
 * vậy chỉ có ở khổ rộng — xem ghi chú ở `payable-list-page`.
 */
export function PayableCard({ row }: { row: Payable }) {
  const source = PAYABLE_SOURCE_LABELS[row.source_type] ?? row.source_type

  return (
    <div className="space-y-1.5">
      <span className="block font-medium text-foreground">
        {row.supplier_name || row.supplier_code || '—'}
      </span>

      {/*  Dấu `·` nằm CÙNG span với vế đứng sau — tách ra thành phần tử riêng
           thì lúc co chữ nó ở lại cuối dòng trên, thành một dấu chấm mồ côi. */}
      <span className="flex min-w-0 flex-wrap items-center gap-1 text-xs text-muted-foreground">
        <span className="font-medium text-sky-600 dark:text-sky-400">{row.po_code || '—'}</span>
        <span>
          <span aria-hidden="true">· </span>
          {source}
        </span>
        {row.invoice_no ? (
          <span>
            <span aria-hidden="true">· </span>
            {row.invoice_no}
          </span>
        ) : (
          //  Chưa có số HĐ = chưa lên được yêu cầu thanh toán. Phải nhìn ra
          //  ngay chứ không để trống như một ô rỗng bình thường — giống hệt
          //  cách cột `invoice_no` của bảng xử lý.
          <span className="text-destructive">
            <span aria-hidden="true">· </span>
            chưa có HĐ
          </span>
        )}
      </span>

      <div className="flex flex-wrap items-center gap-x-2 gap-y-1.5">
        <PayableAgingBadge aging={row.aging} />
        <PayableStatusBadge status={row.status} />
        {row.due_date && (
          <span className="text-xs whitespace-nowrap text-muted-foreground">
            Hạn {formatDate(row.due_date)}
          </span>
        )}
      </div>

      <div className="flex flex-wrap items-baseline justify-between gap-x-2">
        <span className="text-xs text-muted-foreground">
          Còn lại
          {row.paid_amount > 0 && (
            <span className="ml-1">(đã trả {formatMoney(row.paid_amount)} đ)</span>
          )}
        </span>
        <span className="text-sm font-semibold whitespace-nowrap tabular-nums text-foreground">
          {formatMoney(row.remaining)} đ
        </span>
      </div>
    </div>
  )
}
