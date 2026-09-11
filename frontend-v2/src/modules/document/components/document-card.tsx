import { ChevronRight, Copy, Paperclip, ShieldCheck, TriangleAlert } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { formatDate } from '@/shared/utils/format-date'
import { effectiveLabel } from '../helpers/document-status'
import type { DocumentRecord } from '../types/document-record'

interface DocumentCardProps {
  doc: DocumentRecord
  /**
   * Văn bản đang chờ CHÍNH người xem duyệt. Chỉ tab «Văn bản đi» truyền — nó là
   * tab duy nhất nạp hộp việc để biết điều đó.
   */
  awaitingMyApproval?: boolean
  /**
   * Bày *pháp nhân ban hành · phòng chủ trì*. Bật ở tab «Văn bản đi»: ở đó hai ô
   * này là cột thường trực, và với BẢN RIÊNG của pháp nhân con thì pháp nhân là
   * thứ DUY NHẤT phân biệt nó với bản gốc (tiêu đề chép nguyên).
   */
  showOrigin?: boolean
  /**
   * Bày dòng «Cần rà lại». Chỉ tab «Văn bản đến»: đó là lý do chính người ta mở
   * tab đó ra — văn bản mình phải làm theo vừa bị đổi.
   */
  showReviewFlag?: boolean
}

/**
 * Một VĂN BẢN ở chế độ MÀN HẸP — xem `DataTableProps.mobileCard`.
 *
 * Bảng «Văn bản đi» khai **17 cột**, bề rộng tự nhiên ~1934px: trên máy 390px
 * phần nhìn thấy được là cột *Số hiệu* cộng một mẩu *Số vào sổ*, còn *Tên văn
 * bản* — thứ duy nhất nói đây là văn bản gì — nằm sau một lượt cuộn ngang.
 *
 * ⚠️ **TÊN VĂN BẢN LÊN TRƯỚC, số hiệu tụt xuống dòng phụ.** Bảng để *Số hiệu*
 * đứng đầu vì cột đầu là cột định danh và nó được ghim; trên thẻ thì số hiệu là
 * thứ ít dùng nhất, mà tệ hơn: văn bản **chưa duyệt thì chưa có số**, nên cả một
 * danh sách nháp in ra đúng mười dòng «Chưa cấp số» giống hệt nhau — chuỗi dài
 * nhất và ít giá trị nhất lại chiếm dòng đầu. Đây là bài học đã rút ở khối «Văn
 * bản gần đây» của trang Tổng quan Văn thư (duoc-CR-364).
 *
 * ⚠️ **«Chưa cấp số» KHÔNG dùng `font-mono`** — nó là một lời nói, không phải
 * một mã. Chữ đều nét làm nó dãn ra và đọc như lỗi hiển thị; cùng lý do với
 * CR-364.
 *
 * ⚠️ **Mỗi dòng chữ đúng MỘT hàng, dài thì «…»** (luật chung của thẻ, khách chốt
 * 10/09/2026): thẻ cao thấp so le thì mắt phải dò lại mép trên của từng thẻ thay
 * vì lướt một cột đều.
 *
 * ⚠️ **Không nút nào trong thẻ.** `DataTableMobileCards` bọc cả thẻ trong một
 * `<button>`; lồng nút vào trong nút là HTML sai và trên máy cảm ứng thì hai
 * vùng chạm đè nhau. Nên số bản riêng ở đây là một HUY HIỆU đọc được chứ không
 * phải mũi tên bung như ở bảng — mở bản riêng vẫn phải qua màn rộng.
 */
export function DocumentCard({
  doc,
  awaitingMyApproval = false,
  showOrigin = false,
  showReviewFlag = false,
}: DocumentCardProps) {
  //  Nhãn TÍNH RA lúc hiển thị (hết hạn theo ngày) như bảng, không phải trạng
  //  thái thô — thẻ và bảng nói khác nhau về cùng một văn bản là chuyện không
  //  giải thích được với người dùng.
  const label = effectiveLabel(doc)
  const origin = [doc.company_name, doc.department_name].filter(Boolean).join(' · ')
  const cloneCount = doc.clone_count ?? 0
  const hasFooter = Boolean(doc.effective_date) || doc.attachment_count > 0

  return (
    <div className="flex items-start gap-3">
      <div className="min-w-0 flex-1 space-y-1.5">
        <span className="block truncate font-medium text-foreground">{doc.title}</span>

        {/*  Số hiệu + loại trên một dòng phụ. Dấu `·` nằm CÙNG span với vế đứng
             sau nó — tách thành phần tử riêng thì lúc co chữ nó ở lại cuối dòng
             trên, thành một dấu chấm giữa mồ côi treo ở mép phải. */}
        <span className="flex min-w-0 items-center gap-1 text-xs text-muted-foreground">
          {doc.display_code ? (
            <span className="truncate font-mono text-navy">{doc.display_code}</span>
          ) : (
            <span className="shrink-0">Chưa cấp số</span>
          )}
          {doc.doc_type_name && (
            <span className="truncate">
              <span aria-hidden="true">· </span>
              {doc.doc_type_name}
            </span>
          )}
        </span>

        <div className="flex flex-wrap items-center gap-1.5">
          <Badge variant={label.variant}>{label.text}</Badge>

          {/*  «Chờ bạn duyệt» đứng CẠNH trạng thái chứ không thay thế nó: văn bản
               vẫn đang ở «Đang duyệt», thứ thêm vào là *lượt của ai*. */}
          {awaitingMyApproval && (
            <Badge className="gap-1 bg-primary text-primary-foreground">
              <ShieldCheck className="size-3" />
              Chờ bạn duyệt
            </Badge>
          )}

          {showOrigin && cloneCount > 0 && (
            <Badge variant="outline" className="gap-1 font-normal">
              <Copy className="size-3" />
              {cloneCount} bản riêng
            </Badge>
          )}
        </div>

        {showOrigin && origin && (
          <span className="block truncate text-xs text-muted-foreground">{origin}</span>
        )}

        {/*  Cảnh báo phải theo sang thẻ, đừng bỏ vì cho gọn: ở bảng nó là một
             dòng chữ hổ phách dưới trích yếu, ở thẻ phải là một dòng hổ phách —
             không thể là khoảng trắng. */}
        {showReviewFlag && doc.needs_review && (
          <span className="flex items-center gap-1 text-xs text-amber-800">
            <TriangleAlert className="size-3.5 shrink-0" aria-hidden="true" />
            Cần rà lại
          </span>
        )}

        {hasFooter && (
          <div className="flex flex-wrap items-center gap-x-2 text-xs text-muted-foreground">
            {doc.effective_date && (
              <span className="tabular-nums">Hiệu lực {formatDate(doc.effective_date)}</span>
            )}
            {doc.attachment_count > 0 && (
              <span className="flex items-center gap-1">
                <Paperclip className="size-3 shrink-0" aria-hidden="true" />
                {doc.attachment_count}
              </span>
            )}
          </div>
        )}
      </div>

      {/*  Mũi tên nói THẺ NÀY BẤM ĐƯỢC: màn cảm ứng không có con trỏ đổi hình khi
           rê qua, nên phải nói bằng hình. */}
      <ChevronRight className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
    </div>
  )
}
