import { Badge } from '@/shared/ui/badge'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { DocumentStatusBadge, StatusBadge } from './document-status-badge'
import { PO_STATUS_LABELS, type PurchaseOrder } from '../types/purchase-document'

/**
 * Một ĐƠN MUA HÀNG ở khổ điện thoại — xem `DataTableProps.mobileCard`.
 *
 * Bảng khai **13 cột**, bề rộng tự nhiên ~2000px trong khung ~322px: phần nhìn
 * thấy được là *Mã ĐMH* cộng *Ngày đặt*, còn **nhà cung cấp, số tiền và trạng
 * thái** — ba thứ quyết định có mở đơn ra xem hay không — thì nằm ngoài mép
 * phải.
 *
 * ⚠️ **Nhà cung cấp lên dòng đầu, mã đơn tụt xuống dòng phụ** — cùng bài học với
 * `PaymentRequestCard` / `PayableCard`: mã đơn xếp dọc thành một cột `PO001…`
 * chỉ khác nhau hai chữ số cuối, đọc mười dòng không phân biệt được dòng nào;
 * thứ phân biệt chúng là MUA CỦA AI.
 *
 * ⚠️ **Cờ «Gấp» đứng NGAY CẠNH tên NCC**, không dồn xuống hàng huy hiệu bên
 * dưới: đây là thứ bắt mắt phải thấy trước khi đọc gì khác, mà hàng dưới đã có
 * hai huy hiệu trạng thái rồi — thêm cái thứ ba vào đó là nó chìm nghỉm.
 *
 * ⚠️ **Số tiền KHÔNG rút gọn.** Người duyệt bấm dựa trên đúng con số này, mà
 * «201,9 tr» với «201.960.000 đ» là hai mức tin cậy khác nhau.
 *
 * ⚠️ **Không nút nào trong thẻ**: bảng khai `onRowClick` nên `DataTableMobileCards`
 * bọc cả thẻ trong một `<button>`; lồng nút vào trong nút là HTML sai và trên
 * máy cảm ứng hai vùng chạm đè nhau.
 */
export function PurchaseOrderCard({ row }: { row: PurchaseOrder }) {
  const meta = [row.pr_code, row.misa_code].filter(Boolean)

  return (
    <div className="space-y-1.5">
      <span className="flex items-start gap-1.5">
        <span className="line-clamp-2 min-w-0 font-medium text-foreground">
          {row.supplier_name || row.supplier_code || '(chưa chọn NCC)'}
        </span>
        {row.is_urgent && (
          <Badge variant="secondary" className="shrink-0 border-0 bg-warning/10 text-warning">
            Gấp
          </Badge>
        )}
      </span>

      {/*  Dấu `·` nằm CÙNG span với vế đứng sau — tách ra thành phần tử riêng
           thì lúc co chữ nó ở lại cuối dòng trên, thành một dấu chấm mồ côi. */}
      <span className="flex min-w-0 flex-wrap items-center gap-1 text-xs text-muted-foreground">
        <span className="font-medium text-sky-600 dark:text-sky-400">{row.code || '—'}</span>
        {meta.map((text) => (
          <span key={text}>
            <span aria-hidden="true">· </span>
            {text}
          </span>
        ))}
      </span>

      <div className="flex flex-wrap items-center gap-x-2 gap-y-1.5">
        <StatusBadge status={row.status} labels={PO_STATUS_LABELS} />
        <span className="text-sm font-semibold whitespace-nowrap tabular-nums text-foreground">
          {formatMoney(row.amount)} đ
        </span>
        {row.order_date && (
          <span className="text-xs whitespace-nowrap text-muted-foreground">
            {formatDate(row.order_date)}
          </span>
        )}
      </div>

      {/*  ⚠️ **Hồ sơ chứng từ phải đi qua `DocumentStatusBadge`, đừng in thẳng
           `row.document_status`.** Chú thích ở `PurchaseOrder.document_status`
           bảo nó "lưu CHUỖI TIẾNG VIỆT, không phải mã" — dữ liệu thật thì
           ngược lại: trên hệ đang chạy nó ra `none` / `partial`, và in thẳng là
           bày mã tiếng Anh ra cho người dùng. Bảng vốn đã dùng huy hiệu này,
           thẻ phải nói y hệt. */}
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1.5">
        <DocumentStatusBadge status={row.document_status} />
        {row.nspt && <span className="text-xs text-muted-foreground">{row.nspt}</span>}
      </div>
    </div>
  )
}
