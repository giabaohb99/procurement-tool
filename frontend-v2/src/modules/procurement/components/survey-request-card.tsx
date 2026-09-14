import { formatDate } from '@/shared/utils/format-date'
import { StatusBadge } from './document-status-badge'
import { SR_STATUS_LABELS, type SurveyRequest } from '../types/purchase-document'

/**
 * Một YÊU CẦU BÁO GIÁ ở khổ điện thoại — xem `DataTableProps.mobileCard`.
 *
 * Bảng khai **8 cột**, bề rộng tự nhiên ~1330px trong khung ~322px: phần nhìn
 * thấy được là *Mã phiếu* cộng một mẩu *Mục đích*, còn **trạng thái** — thứ
 * quyết định phiếu này còn việc gì để làm hay không — thì nằm ngoài mép phải.
 *
 * ⚠️ **Mục đích lên dòng đầu, mã phiếu tụt xuống dòng phụ** — cùng bài học với
 * `SurveyCard` / `PurchaseRequestCard`: mã phiếu xếp dọc thành một cột
 * `YCBGDEMO0…` chỉ khác nhau hai chữ số cuối, đọc mười dòng không phân biệt
 * được dòng nào; thứ phân biệt chúng là ĐANG HỎI GIÁ CÁI GÌ.
 *
 * ⚠️ **Ngày đọc từ `created_at`, KHÔNG từ `request_date`** — đúng như cột *Ngày
 * tạo* của bảng. Hai ô này khác nhau: `request_date` là ngày người lập tự khai,
 * bỏ trống được; `created_at` là dấu vết hệ thống, luôn có.
 *
 * ⚠️ **Không nút nào trong thẻ**: bảng khai `onRowClick` nên `DataTableMobileCards`
 * bọc cả thẻ trong một `<button>`; lồng nút vào trong nút là HTML sai và trên
 * máy cảm ứng hai vùng chạm đè nhau. Nút *Nhân bản* của cột thao tác vì vậy chỉ
 * còn ở khổ rộng — việc hiếm, và vẫn làm được trong trang chi tiết.
 */
export function SurveyRequestCard({ row }: { row: SurveyRequest }) {
  const meta = [row.requester, row.department].filter(Boolean)

  return (
    <div className="space-y-1.5">
      {/*  ⚠️ Chỉ `line-clamp-2`, KHÔNG kèm `block`: cả hai cùng đặt `display`
           (`-webkit-box` với `block`) nên chúng chọi nhau và clamp im lặng mất
           tác dụng — mục đích dài vẫn xuống bốn dòng, không lỗi, không cảnh báo. */}
      <span className="line-clamp-2 font-medium text-foreground">
        {row.purpose || row.code || '—'}
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
        <StatusBadge status={row.status} labels={SR_STATUS_LABELS} />
        {row.created_at && (
          <span className="text-xs whitespace-nowrap text-muted-foreground">
            {formatDate(row.created_at)}
          </span>
        )}
      </div>
    </div>
  )
}
