import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { PaymentRequestStatusBadge } from './payment-request-status-badge'
import {
  PAYMENT_METHOD_LABELS,
  PAYMENT_SOURCE_LABELS,
  type PaymentRequestSummary,
} from '../types/payment-request'

/**
 * Một YÊU CẦU THANH TOÁN ở khổ điện thoại — xem `DataTableProps.mobileCard`.
 *
 * Bảng khai **11 cột**, bề rộng tự nhiên ~1750px trong khung ~322px: phần nhìn
 * thấy được là *Mã phiếu · Ngày lập* cộng một mẩu *Người yêu cầu*, còn **nhà
 * cung cấp, SỐ TIỀN và trạng thái** — ba thứ quyết định có duyệt chi hay không
 * — thì nằm ngoài mép phải.
 *
 * ⚠️ **Nhà cung cấp lên dòng đầu, mã phiếu tụt xuống dòng phụ** — cùng bài học
 * với `DocumentCard` / `ApprovalInboxCard`: mã phiếu xếp dọc thành một cột
 * `YCTT000…` chỉ khác nhau hai chữ số cuối, không nói được phiếu nào là phiếu
 * nào; thứ phân biệt chúng là TRẢ CHO AI.
 *
 * ⚠️ **Số tiền KHÔNG rút gọn.** Người duyệt bấm dựa trên đúng con số này, mà
 * «1,2 tr» với «1.234.567 đ» là hai mức tin cậy khác nhau khi thứ theo sau là
 * một chữ ký chi tiền.
 *
 * ⚠️ **Không nút nào trong thẻ**: `DataTableMobileCards` bọc cả thẻ trong một
 * `<button>` (bảng này có `onRowClick`), lồng nút vào trong nút là HTML sai và
 * trên máy cảm ứng hai vùng chạm đè nhau.
 */
export function PaymentRequestCard({ row }: { row: PaymentRequestSummary }) {
  const source = PAYMENT_SOURCE_LABELS[row.source_type] ?? row.source_type
  const method = PAYMENT_METHOD_LABELS[row.payment_method] ?? row.payment_method

  return (
    <div className="space-y-1.5">
      <span className="block truncate font-medium text-foreground">
        {row.supplier_name || row.supplier_code || '—'}
      </span>

      {/*  Dấu `·` nằm CÙNG span với vế đứng sau — tách ra thành phần tử riêng
           thì lúc co chữ nó ở lại cuối dòng trên, thành một dấu chấm mồ côi. */}
      <span className="flex min-w-0 flex-wrap items-center gap-1 text-xs text-muted-foreground">
        <span className="font-medium text-sky-600 dark:text-sky-400">{row.code || '—'}</span>
        {row.request_date && (
          <span>
            <span aria-hidden="true">· </span>
            {formatDate(row.request_date)}
          </span>
        )}
        {row.created_by_name && (
          <span className="truncate">
            <span aria-hidden="true">· </span>
            {row.created_by_name}
          </span>
        )}
      </span>

      <div className="flex flex-wrap items-center gap-x-2 gap-y-1.5">
        <PaymentRequestStatusBadge status={row.status} />
        <span className="text-sm font-semibold whitespace-nowrap tabular-nums text-foreground">
          {formatMoney(row.total)} đ
        </span>
        {/*  Loại nợ và hình thức chi đứng CUỐI: chúng phân loại phiếu chứ không
             quyết định bấm hay không, mà dòng trên đã kín chỗ. */}
        <span className="text-xs text-muted-foreground">
          {source} · {method}
        </span>
      </div>
    </div>
  )
}
