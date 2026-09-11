import { ChevronRight } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'

interface CatalogCardProps {
  /** Dòng đầu — thứ người dùng dò khi lướt danh sách. */
  title: string
  /** Mã của bản ghi. Bỏ trống thì dòng phụ chỉ còn `meta`. */
  code?: string
  /**
   * Vài mẩu ngữ cảnh NGẮN, nối nhau bằng `·` trên cùng dòng phụ với mã.
   * Mẩu rỗng tự bị bỏ, nên nơi gọi cứ truyền thẳng trường có thể trống.
   */
  meta?: (string | undefined | null)[]
  isActive: boolean
  /** Dòng chữ dài ở cuối (mô tả). Cắt đúng một dòng. */
  note?: string
}

/**
 * Một dòng DANH MỤC NỀN ở chế độ màn hẹp — xem `CatalogTableProps.mobileCard`.
 *
 * Dùng chung cho cả bốn danh mục của *Thiết lập văn bản* (loại văn bản · thư
 * viện mẫu · mức mật/khẩn · đơn vị gửi nhận) và mở được cho danh mục khác của
 * phân hệ. Bốn bảng đó khai cột khác nhau nhưng **cùng một hình**: một mã, một
 * tên, vài thuộc tính ngắn, một huy hiệu *Đang dùng / Ngừng*. Dựng bốn thẻ riêng
 * là chép bốn lần cùng một khung rồi để chúng trôi khỏi nhau.
 *
 * ⚠️ **TÊN lên trước, mã xuống dòng phụ.** Bảng để *Mã* ở cột đầu vì cột đầu là
 * cột định danh và được ghim; trên thẻ thì mã là thứ ít dùng hơn — người ta tìm
 * «Quyết định» chứ ít khi tìm «QD». Cùng bài học với `DocumentCard` (CR-364/365).
 *
 * ⚠️ **Mỗi dòng chữ đúng MỘT hàng, dài thì «…»** — thẻ cao thấp so le thì mắt
 * phải dò lại mép trên của từng thẻ thay vì lướt một cột đều.
 *
 * ⚠️ **Không nút nào trong thẻ**: `DataTableMobileCards` bọc cả thẻ trong một
 * `<button>`, lồng nút vào trong nút là HTML sai và trên máy cảm ứng thì hai
 * vùng chạm đè nhau.
 */
export function CatalogCard({ title, code, meta, isActive, note }: CatalogCardProps) {
  //  Lọc mẩu rỗng NGAY TẠI ĐÂY chứ không bắt bốn nơi gọi tự lo: trường như
  //  `contact_person`, `phone` của đơn vị gửi nhận thường để trống, mà nối thẳng
  //  thì ra chuỗi «· ·» — một dãy dấu chấm giữa không có chữ nào ở giữa.
  const parts = (meta ?? []).map((item) => item?.trim()).filter(Boolean)

  return (
    <div className="flex items-start gap-3">
      <div className="min-w-0 flex-1 space-y-1.5">
        <span className="block truncate font-medium text-foreground">{title}</span>

        {(code || parts.length > 0) && (
          //  Dấu `·` nằm CÙNG span với vế đứng sau nó — tách thành phần tử riêng
          //  thì lúc co chữ nó ở lại cuối dòng trên, thành một dấu chấm giữa mồ
          //  côi treo ở mép phải.
          <span className="flex min-w-0 items-center gap-1 text-xs text-muted-foreground">
            {/*  ⚠️ `shrink-0` cho MÃ — nó là chuỗi ngắn nhất nhưng lại là thứ
                 định danh dòng, để nó co cùng mấy vế kia thì gặp dòng dài là ra
                 «B…» (đo thấy ở loại *Bản ghi nhớ*, mã `BGN`): ba ký tự bị cắt
                 còn một, không còn nhận ra là mã gì. Phần bị chật để mấy vế sau
                 gánh — chúng dài và cắt đuôi vẫn đoán được. */}
            {code && <span className="shrink-0 font-mono text-navy">{code}</span>}
            {parts.map((part, index) => (
              <span key={part} className="truncate">
                {(code || index > 0) && <span aria-hidden="true">· </span>}
                {part}
              </span>
            ))}
          </span>
        )}

        <div className="flex flex-wrap items-center gap-1.5">
          <Badge variant={isActive ? 'default' : 'secondary'}>
            {isActive ? 'Đang dùng' : 'Ngừng'}
          </Badge>
        </div>

        {note && <span className="block truncate text-xs text-muted-foreground">{note}</span>}
      </div>

      {/*  Mũi tên nói THẺ NÀY BẤM ĐƯỢC: màn cảm ứng không có con trỏ đổi hình khi
           rê qua, nên phải nói bằng hình. */}
      <ChevronRight className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
    </div>
  )
}
