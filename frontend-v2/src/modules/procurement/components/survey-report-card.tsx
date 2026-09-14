import { Badge } from '@/shared/ui/badge'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { LineApproveBadge } from './document-status-badge'
import type { SurveyReportLine } from '../types/survey-report'

const KIND_LABELS: Record<string, string> = { supplier: 'NCC', product: 'SP' }

/**
 * Một DÒNG khảo sát ở khổ điện thoại — xem `DataTableProps.mobileCard`.
 *
 * Báo cáo khai **~40 cột**, bề rộng tự nhiên vài nghìn pixel trong khung ~322px:
 * phần nhìn thấy được là *Mã phiếu · Loại* cộng một mẩu *Nội dung dòng*, còn
 * **kết quả duyệt** — thứ cả màn hình này sinh ra để trả lời — thì nằm ngoài
 * mép phải.
 *
 * ⚠️ **Thẻ RẼ theo `kind`.** Dòng NCC và dòng SP có tập trường lệch nhau gần
 * hết (xem ghi chú đầu `survey-report.ts`): NCC có MST / người liên hệ, SP có
 * đơn giá / MOQ / ĐVT báo giá. Dùng chung một khuôn thì mỗi thẻ bỏ trắng đúng
 * nửa số ô — mà backend trả ĐỦ bộ khóa cho cả hai loại nên ô trắng đó không nổ,
 * chỉ lặng lẽ vô nghĩa. Chỉ dòng CUỐI đổi theo loại; ba dòng trên giữ nguyên để
 * hai loại vẫn đọc được thành một danh sách.
 *
 * ⚠️ **Không nút, không liên kết nào trong thẻ.** Bảng khai `onRowClick` ở khổ
 * hẹp (mở phiếu khảo sát) nên `DataTableMobileCards` bọc CẢ THẺ trong một
 * `<button>`; lồng `<a>` hay `<button>` vào trong đó là HTML sai và trên máy
 * cảm ứng hai vùng chạm đè nhau. Mã phiếu vì vậy là chữ thường — muốn mở phiếu
 * thì chạm bất kỳ đâu trên thẻ. (Ở khổ rộng cột *Mã phiếu* của bảng vẫn là liên
 * kết như cũ, vì bảng KHÔNG bật `onRowClick` ở khổ đó.)
 *
 * ⚠️ **Số 0 tới đây đã là `null`** (`to_report_number` ở backend quy 0 về None
 * để ô bỏ trắng). Nên kiểm `!= null` chứ đừng kiểm truthy trên số đã định dạng,
 * và đừng in "0 đ" cho dòng NCC vốn không có khái niệm đơn giá.
 */
export function SurveyReportCard({ row }: { row: SurveyReportLine }) {
  const kindLabel = KIND_LABELS[row.kind] ?? row.kind

  return (
    <div className="space-y-1.5">
      <div className="flex items-start justify-between gap-2">
        {/*  Cắt ở ĐÚNG HAI DÒNG rồi bỏ lửng bằng "…".

             `line-clamp-2` chứ không `truncate`: tên sản phẩm khảo sát dài
             thật (quy cách + kích thước nằm ngay trong tên), cắt còn MỘT dòng
             thì mọi thẻ mở đầu như nhau — «Thùng carton 5 lớp sóng BC, in…» —
             và không phân biệt được dòng nào là dòng nào. Hai dòng đủ tới phần
             khác nhau. Cũng không để xuống dòng tự do: một tên bốn dòng đẩy
             phần dưới của thẻ ra khỏi tầm mắt, mà thứ quyết định ở đây là kết
             quả duyệt và con số bên dưới.

             `title` để bản đầy đủ vẫn lấy được — trên máy tính là chỉ dẫn khi
             rê chuột, và trình đọc màn hình đọc được trọn tên. */}
        <span className="line-clamp-2 min-w-0 font-medium text-foreground" title={row.content}>
          {row.content || '—'}
        </span>
        <Badge variant="outline" className="shrink-0">
          {kindLabel}
        </Badge>
      </div>

      {/*  Dấu `·` nằm CÙNG span với vế đứng sau — tách ra thành phần tử riêng
           thì lúc co chữ nó ở lại cuối dòng trên, thành một dấu chấm mồ côi. */}
      <span className="flex min-w-0 flex-wrap items-center gap-1 text-xs text-muted-foreground">
        {/*  CHỮ THƯỜNG, không phải liên kết — xem ghi chú đầu tệp. Cả thẻ đã
             là một nút mở phiếu rồi; lồng thêm `<Link>` vào trong `<button>`
             là HTML sai và trên máy cảm ứng hai vùng chạm đè nhau. Vẫn tô màu
             nhấn để mã phiếu nổi lên giữa dòng chữ mờ. */}
        <span className="font-medium text-primary">{row.survey_code || '—'}</span>
        {row.kind === 'product' ? (
          <>
            {row.internal_code && (
              <span>
                <span aria-hidden="true">· </span>
                {row.internal_code}
              </span>
            )}
            {row.quote_unit && (
              <span>
                <span aria-hidden="true">· </span>
                {row.quote_unit}
              </span>
            )}
          </>
        ) : (
          row.sr_code && (
            <span>
              <span aria-hidden="true">· </span>
              {row.sr_code}
            </span>
          )
        )}
      </span>

      <div className="flex flex-wrap items-center gap-x-2 gap-y-1.5">
        <LineApproveBadge status={row.line_approve} />
        {row.date && (
          <span className="text-xs whitespace-nowrap text-muted-foreground">
            {formatDate(row.date)}
          </span>
        )}
      </div>

      <SurveyReportCardFacts row={row} />
    </div>
  )
}

/**
 * Dòng CUỐI của thẻ — phần đổi theo loại dòng.
 *
 * Tách hàm riêng vì đây là chỗ duy nhất hai loại rẽ nhánh; để lẫn trong thân
 * thẻ thì mỗi lần thêm một trường lại phải dò xem nhánh nào đang đọc trường của
 * loại nào.
 *
 * Trả `null` khi không có gì để nói — thà thẻ ngắn một dòng còn hơn chừa một
 * khoảng trắng làm người đọc tưởng dữ liệu chưa tải xong.
 */
function SurveyReportCardFacts({ row }: { row: SurveyReportLine }) {
  const facts: string[] = []

  if (row.kind === 'product') {
    //  Đơn giá dùng `formatUnitPrice` (giữ tới 4 số lẻ) đúng như cột "Đơn giá"
    //  của bảng — `formatMoney` làm tròn tới đồng và nuốt mất phần lẻ của giá.
    if (row.price_by_volume != null) {
      const unit = row.quote_unit ? `/${row.quote_unit}` : ''
      facts.push(`${formatUnitPrice(row.price_by_volume)} đ${unit}`)
    }
    if (row.moq != null) facts.push(`MOQ ${formatQuantity(row.moq)}`)
    if (row.origin) facts.push(row.origin)
  } else {
    if (row.tax_code) facts.push(`MST ${row.tax_code}`)
    if (row.contact_person) facts.push(row.contact_person)
    if (row.debt_policy) facts.push(`Công nợ ${row.debt_policy}`)
  }

  if (!facts.length) return null

  return (
    <p className="text-xs text-muted-foreground">
      {facts.map((fact, index) => (
        <span key={fact}>
          {index > 0 && <span aria-hidden="true"> · </span>}
          {fact}
        </span>
      ))}
    </p>
  )
}
