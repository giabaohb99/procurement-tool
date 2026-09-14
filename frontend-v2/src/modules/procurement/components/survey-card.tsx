import { StatusBadge } from './document-status-badge'
import { formatDate } from '@/shared/utils/format-date'
import {
  SURVEY_STATUS_LABELS,
  SURVEY_TYPE_LABELS,
  type Survey,
} from '../types/purchase-document'

/**
 * Một PHIẾU KHẢO SÁT ở khổ điện thoại — xem `DataTableProps.mobileCard`.
 *
 * Bảng khai **11 cột**, bề rộng tự nhiên ~1700px trong khung ~322px: phần nhìn
 * thấy được là *Mã phiếu* cộng một mẩu *Loại*, còn **nội dung khảo sát và trạng
 * thái** — hai thứ để nhận ra phiếu nào là phiếu nào — thì nằm ngoài mép phải.
 *
 * ⚠️ **Nội dung chính lên dòng đầu, mã phiếu tụt xuống dòng phụ** — cùng bài học
 * với `PaymentRequestCard` / `DocumentCard`: mã phiếu xếp dọc thành một cột
 * `KSDEMO0…` chỉ khác nhau hai chữ số cuối, đọc mười dòng không phân biệt được
 * dòng nào; thứ phân biệt chúng là KHẢO SÁT CÁI GÌ.
 *
 * ⚠️ **`line-clamp-2` cho nội dung chính**: ô này là câu mô tả tự do, có phiếu
 * dài vài dòng. Để xuống dòng tự do thì một thẻ cao gấp ba thẻ bên cạnh và cả
 * danh sách mất nhịp; cắt còn một dòng thì mọi phiếu mở đầu bằng «Khảo sát…»
 * giống hệt nhau.
 *
 * ⚠️ **Không nút nào trong thẻ**: bảng khai `onRowClick` (mở chi tiết phiếu) nên
 * `DataTableMobileCards` bọc cả thẻ trong một `<button>`; lồng nút vào trong nút
 * là HTML sai và trên máy cảm ứng hai vùng chạm đè nhau. Nút *Nhân bản* vì vậy
 * chỉ có ở khổ rộng — xem ghi chú ở `survey-list-page`.
 */
export function SurveyCard({ row }: { row: Survey }) {
  const type = SURVEY_TYPE_LABELS[row.survey_type] ?? row.survey_type

  return (
    <div className="space-y-1.5">
      <span className="line-clamp-2 block font-medium text-foreground">
        {row.main_content || row.code || '—'}
      </span>

      {/*  Dấu `·` nằm CÙNG span với vế đứng sau — tách ra thành phần tử riêng
           thì lúc co chữ nó ở lại cuối dòng trên, thành một dấu chấm mồ côi. */}
      <span className="flex min-w-0 flex-wrap items-center gap-1 text-xs text-muted-foreground">
        <span className="font-medium text-sky-600 dark:text-sky-400">{row.code || '—'}</span>
        {row.sr_code && (
          <span>
            <span aria-hidden="true">· </span>
            {row.sr_code}
          </span>
        )}
        {row.item_code && (
          <span>
            <span aria-hidden="true">· </span>
            {row.item_code}
          </span>
        )}
      </span>

      <div className="flex flex-wrap items-center gap-x-2 gap-y-1.5">
        <StatusBadge status={row.status} labels={SURVEY_STATUS_LABELS} />
        <span className="text-xs text-muted-foreground">{type}</span>
        {row.created_at && (
          <span className="text-xs whitespace-nowrap text-muted-foreground">
            {formatDate(row.created_at)}
          </span>
        )}
      </div>

      {/*  Nhóm hàng + người phụ trách: hai ô để LỌC và để biết hỏi ai, không
           phải thứ quyết định mở phiếu hay không — nên đứng cuối, và vắng thì
           bỏ hẳn dòng chứ đừng chừa một khoảng trắng. */}
      {(row.item_group || row.nspt) && (
        <span className="block text-xs text-muted-foreground">
          {[row.item_group, row.nspt].filter(Boolean).join(' · ')}
        </span>
      )}
    </div>
  )
}
