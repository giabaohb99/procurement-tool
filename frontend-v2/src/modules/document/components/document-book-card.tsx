import { ChevronRight, Users } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import type { DocumentBook } from '../types/document-book'

interface DocumentBookCardProps {
  book: DocumentBook
  /** Năm đang xem — cùng con số mà cột «Đã cấp {year}» của bảng bày. */
  year: string
}

/**
 * Một SỔ VĂN BẢN ở chế độ MÀN HẸP — xem `DataTableProps.mobileCard`.
 *
 * Bảng khai 8 cột, bề rộng tự nhiên **1180px**: trên máy 393px nhìn thấy được
 * *Mã sổ* và một mẩu *Tên sổ*, còn **Số kế tiếp** — con số người ta mở màn này
 * ra để xem — nằm sau một lượt cuộn ngang.
 *
 * ⚠️ **«Số kế tiếp» là dòng quan trọng nhất của thẻ**, nên nó được cỡ chữ riêng
 * chứ không lẫn vào hàng chữ mờ bên dưới. Cả màn Sổ văn bản tồn tại để trả lời
 * *"sổ này đang tới số mấy"*; mọi thứ còn lại là ngữ cảnh.
 *
 * ⚠️ **«Chưa cử ai» phải nói thành lời.** Sổ mở từ trước lúc bắt buộc cử người
 * quản lý thì mảng rỗng — để ô trống thì nó đọc ra như dữ liệu chưa tải xong,
 * trong khi đây là thứ cần đi sửa. Giữ nguyên câu của bảng.
 *
 * ⚠️ **Không nút nào trong thẻ**: `DataTableMobileCards` bọc cả thẻ trong một
 * `<button>`, lồng nút vào trong nút là HTML sai.
 */
export function DocumentBookCard({ book, year }: DocumentBookCardProps) {
  return (
    <div className="flex items-start gap-3">
      <div className="min-w-0 flex-1 space-y-1.5">
        <span className="block truncate font-medium text-foreground">{book.name}</span>

        {/*  Mã sổ + pháp nhân trên một dòng phụ. Dấu `·` nằm CÙNG span với vế
             đứng sau nó — tách ra thì lúc co chữ nó ở lại cuối dòng trên, thành
             một dấu chấm giữa mồ côi treo ở mép phải. */}
        <span className="flex min-w-0 items-center gap-1 text-xs text-muted-foreground">
          <span className="truncate font-mono text-navy">{book.code}</span>
          {book.company_name && (
            <span className="truncate">
              <span aria-hidden="true">· </span>
              {book.company_name}
            </span>
          )}
        </span>

        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
          <span className="font-mono text-navy dark:text-foreground">
            {book.next_number_display}
          </span>
          <span className="text-xs text-muted-foreground tabular-nums">
            Đã cấp {year}: {book.issued_count}
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          <Badge variant={book.is_active ? 'default' : 'secondary'}>
            {book.is_active ? 'Đang dùng' : 'Ngừng'}
          </Badge>
        </div>

        <span className="flex min-w-0 items-center gap-1 text-xs text-muted-foreground">
          <Users className="size-3 shrink-0" aria-hidden="true" />
          <span className="truncate">
            {book.manager_names.length ? book.manager_names.join(', ') : 'Chưa cử ai'}
          </span>
        </span>
      </div>

      {/*  Mũi tên nói THẺ NÀY BẤM ĐƯỢC: màn cảm ứng không có con trỏ đổi hình khi
           rê qua, nên phải nói bằng hình. */}
      <ChevronRight className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
    </div>
  )
}
