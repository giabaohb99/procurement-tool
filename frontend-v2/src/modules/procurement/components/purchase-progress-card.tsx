import { ProgressStatusBadge } from './document-status-badge'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity } from '@/shared/utils/format-money'
import { cn } from '@/shared/utils/cn'
import type { PurchaseProgressRow } from '../types/purchase-progress'

/**
 * Một LẦN GIAO của một dòng đơn mua hàng, ở khổ điện thoại — xem
 * `DataTableProps.mobileCard`.
 *
 * Bảng khai **26 cột**, bề rộng tự nhiên ~3600px trong khung ~322px: phần nhìn
 * thấy được là *Mã ĐMH* cộng một mẩu *Mã PYC*, còn **tiến độ, số đã nhận và
 * chênh lệch ngày** — cả ba lý do người ta mở màn này — thì nằm ngoài mép phải.
 *
 * ⚠️ **Tên sản phẩm lên dòng đầu, mã ĐMH tụt xuống dòng phụ.** Một ĐMH ba dòng
 * hàng giao hai đợt ra SÁU dòng ở đây, tất cả cùng một mã ĐMH — xếp mã lên đầu
 * thì sáu thẻ liền nhau mở đầu giống hệt nhau. Thứ phân biệt chúng là MẶT HÀNG
 * nào, giao LẦN mấy.
 *
 * ⚠️ **«Lần giao» phải có mặt** dù ở bảng nó là cột `defaultHidden`: trên bảng
 * người ta phân biệt các đợt bằng vị trí dòng và cột Ngày nhận đứng cạnh nhau,
 * còn thẻ thì mỗi cái một khối rời — thiếu số lần thì hai đợt của cùng một mặt
 * hàng không có gì khác nhau ngoài con số đã nhận.
 *
 * ⚠️ **Chênh lệch ngày giữ nguyên DẤU và màu** (`diff_regulated`): âm là trễ,
 * dương là sớm. Bỏ dấu đi thì một đợt trễ 5 ngày đọc ra y như một đợt sớm 5
 * ngày — cùng luật `DiffCell` của bảng.
 */
export function PurchaseProgressCard({ row }: { row: PurchaseProgressRow }) {
  const meta = [row.po_code, row.product_code].filter(Boolean)
  if (row.delivery_no) meta.push(`Lần ${row.delivery_no}`)

  return (
    <div className="space-y-1.5">
      <span className="line-clamp-2 block font-medium text-foreground">
        {row.product_name || row.product_code || '—'}
      </span>

      {/*  Dấu `·` nằm CÙNG span với vế đứng sau — tách ra thành phần tử riêng
           thì lúc co chữ nó ở lại cuối dòng trên, thành một dấu chấm mồ côi. */}
      <span className="flex min-w-0 flex-wrap items-center gap-1 text-xs text-muted-foreground">
        <span className="font-medium text-sky-600 dark:text-sky-400">{row.po_code || '—'}</span>
        {meta.slice(1).map((text) => (
          <span key={text}>
            <span aria-hidden="true">· </span>
            {text}
          </span>
        ))}
      </span>

      <div className="flex flex-wrap items-center gap-x-2 gap-y-1.5">
        <ProgressStatusBadge status={row.progress_status} />
        <span className="text-xs whitespace-nowrap tabular-nums text-muted-foreground">
          Nhận {formatQuantity(row.received_qty)}/{formatQuantity(row.qty_order)}
          {row.unit ? ` ${row.unit}` : ''}
        </span>
        {row.diff_regulated !== 0 && (
          <span
            className={cn(
              'text-xs whitespace-nowrap tabular-nums',
              row.diff_regulated < 0 ? 'text-destructive' : 'text-success',
            )}
            title={row.diff_regulated < 0 ? 'Trễ so với ngày quy định' : 'Sớm so với ngày quy định'}
          >
            {row.diff_regulated > 0 ? `+${row.diff_regulated}` : row.diff_regulated} ngày
          </span>
        )}
      </div>

      {/*  NCC đứng DÒNG RIÊNG, không ghép chung hàng với mấy mốc ngày.
           `line-clamp-1` biến nó thành một khối chiếm trọn bề ngang, nên vế
           đứng sau bị đẩy xuống hàng dưới và mở đầu bằng đúng dấu `·` phân
           cách — một dấu chấm mồ côi ở đầu dòng, trông như lỗi vẽ.

           ⚠️ Phải kiểm RỖNG chứ đừng dựng sẵn nhãn: backend xóa trắng tên NCC
           khi người xem thiếu quyền `supplier.read` (xem
           `PurchaseProgressResult.show_supplier`), dựng sẵn là thẻ hiện một
           dòng trống trơn. */}
      {/*  ⚠️ Chỉ `line-clamp-2`, KHÔNG kèm `block`: cả hai cùng đặt `display`
           (`-webkit-box` với `block`) nên chúng chọi nhau và clamp im lặng mất
           tác dụng — tên NCC dài vẫn xuống bốn dòng, không lỗi, không cảnh báo.
           `line-clamp-*` tự lo phần hiển thị khối. */}
      {row.supplier_name && (
        <span className="line-clamp-2 text-xs text-muted-foreground">{row.supplier_name}</span>
      )}

      {(row.order_date || row.received_date) && (
        <span className="block text-xs whitespace-nowrap text-muted-foreground">
          {[
            row.order_date && `ĐH ${formatDate(row.order_date)}`,
            row.received_date && `Nhận ${formatDate(row.received_date)}`,
          ]
            .filter(Boolean)
            .join(' · ')}
        </span>
      )}
    </div>
  )
}
