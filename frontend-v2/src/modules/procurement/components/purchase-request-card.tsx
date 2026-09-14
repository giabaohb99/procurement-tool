import { Badge } from '@/shared/ui/badge'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { StatusBadge } from './document-status-badge'
import { PR_STATUS_LABELS, type PurchaseRequest } from '../types/purchase-document'

/**
 * Một YÊU CẦU MUA HÀNG ở khổ điện thoại — xem `DataTableProps.mobileCard`.
 *
 * Bảng khai **12 cột**, bề rộng tự nhiên ~1800px trong khung ~322px: phần nhìn
 * thấy được là *Mã PYC* cộng *Ngày tạo*, còn **mục đích, số tiền và trạng thái**
 * — ba thứ quyết định có mở phiếu ra xem hay không — thì nằm ngoài mép phải.
 *
 * ⚠️ **Mục đích lên dòng đầu, mã phiếu tụt xuống dòng phụ** — cùng bài học với
 * `SurveyCard` / `PurchaseOrderCard`: mã phiếu xếp dọc thành một cột `PYC…` chỉ
 * khác nhau vài chữ số cuối, đọc mười dòng không phân biệt được dòng nào; thứ
 * phân biệt chúng là YÊU CẦU MUA GÌ.
 *
 * ⚠️ **Hai cờ cảnh báo đứng CẠNH tiêu đề, không dồn xuống hàng huy hiệu**:
 * *Gấp* và *Có dòng hủy* là thứ phải thấy trước khi đọc gì khác, mà hàng dưới
 * đã có huy hiệu trạng thái rồi.
 *
 * ⚠️ **`has_cancelled_line` là CỜ CỦA DÒNG CON, không phải trạng thái phiếu.**
 * Phiếu vẫn có thể *Đã duyệt* mà bên trong có một dòng đã hủy — bảng cũ tô đỏ
 * cả dòng vì lý do đó. Bỏ cờ này đi thì trên điện thoại không còn dấu hiệu nào,
 * và người duyệt đọc tổng tiền tưởng là tiền của mọi dòng.
 *
 * ⚠️ **Không nút nào trong thẻ**: bảng khai `onRowClick` nên `DataTableMobileCards`
 * bọc cả thẻ trong một `<button>`; lồng nút vào trong nút là HTML sai và trên
 * máy cảm ứng hai vùng chạm đè nhau.
 */
export function PurchaseRequestCard({ row }: { row: PurchaseRequest }) {
  const meta = [row.requester, row.department].filter(Boolean)

  return (
    <div className="space-y-1.5">
      <span className="flex flex-wrap items-start gap-1.5">
        <span className="line-clamp-2 min-w-0 font-medium text-foreground">
          {row.purpose || row.code || '—'}
        </span>
        {row.is_urgent && (
          <Badge variant="secondary" className="shrink-0 border-0 bg-warning/10 text-warning">
            Gấp
          </Badge>
        )}
        {row.has_cancelled_line && (
          <Badge
            variant="secondary"
            className="shrink-0 border-0 bg-destructive/10 text-destructive"
          >
            Có dòng hủy
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
        <StatusBadge status={row.status} labels={PR_STATUS_LABELS} />
        <span className="text-sm font-semibold whitespace-nowrap tabular-nums text-foreground">
          {formatMoney(row.total)} đ
        </span>
        {row.request_date && (
          <span className="text-xs whitespace-nowrap text-muted-foreground">
            {formatDate(row.request_date)}
          </span>
        )}
      </div>

      {/*  Ngày cần hàng đứng riêng vì nó là MỐC HẸN, khác hẳn ngày lập ở hàng
           trên — gộp chung một hàng thì hai con số cùng dạng nằm cạnh nhau và
           không có gì nói cái nào là cái nào. */}
      {row.need_date && (
        <span className="block text-xs text-muted-foreground">
          Cần hàng {formatDate(row.need_date)}
        </span>
      )}
    </div>
  )
}
