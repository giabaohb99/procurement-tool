import { ChevronRight, Clock, UserRound } from 'lucide-react'

import { ACTION_TONE } from '@/modules/approval/helpers/decision-tone'
import { Badge } from '@/shared/ui/badge'
import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import type { InboxRow } from './approval-inbox-row'

/**
 * Một dòng HỘP DUYỆT ở chế độ MÀN HẸP — xem `DataTableProps.mobileCard`.
 *
 * Bảng khai 10 cột, bề rộng tự nhiên **1450px**: trên máy 390px phần nhìn thấy
 * được là cột *Số hiệu* cộng một mẩu *Tên văn bản*, còn cột ghim *Tình trạng*
 * đứng đè lên ngay sau đó. Tức người dùng thấy đúng hai thứ — một mã và một huy
 * hiệu — mà không thấy **mình phải duyệt cái gì**.
 *
 * ⚠️ **TÊN VĂN BẢN LÊN TRƯỚC, số hiệu tụt xuống dòng phụ** — cùng lý do và cùng
 * bài học với `DocumentCard` (duoc-CR-364/365). Ở đây còn nặng hơn: hộp duyệt
 * phần lớn là văn bản **đang trình, chưa cấp số**, nên cột đầu của bảng in ra
 * một dãy «Chưa cấp số» giống hệt nhau — dòng định danh mà không định danh được
 * dòng nào.
 *
 * ⚠️ **«Chưa cấp số» KHÔNG dùng `font-mono`**: nó là một lời nói, không phải một
 * mã. Chữ đều nét làm nó dãn ra và đọc như lỗi hiển thị.
 *
 * ⚠️ **Hai loại dòng bày HAI bộ trường khác nhau** — đây là chỗ thẻ làm được mà
 * bảng gộp không làm được. Bảng phải có đủ cột cho cả hai loại rồi vẽ "—" vào
 * những ô loại kia không có, nên mở ở khổ hẹp là gặp một rừng gạch ngang. Thẻ
 * chỉ dựng dòng nào có nghĩa với chính nó: việc CHỜ nói *ai trình · hạn nào*,
 * việc ĐÃ BẤM nói *bấm lúc nào · phiếu giờ ra sao*.
 *
 * ⚠️ **Huy hiệu tình trạng phải còn nguyên trên thẻ.** Ở bảng nó là cột duy nhất
 * không ẩn được và được ghim phải, vì nó là thứ DUY NHẤT phân biệt hai nửa của
 * bảng gộp. Bỏ nó khỏi thẻ cho gọn là xóa luôn ranh giới giữa *«việc cần làm»*
 * và *«việc đã xong»* — trong khi đó chính là câu hỏi người ta mở màn này ra để
 * trả lời.
 *
 * ⚠️ **Không nút nào trong thẻ**: `DataTableMobileCards` bọc cả thẻ trong một
 * `<button>`, lồng nút vào trong nút là HTML sai và trên máy cảm ứng thì hai
 * vùng chạm đè nhau.
 */
export function ApprovalInboxCard({ row }: { row: InboxRow }) {
  const pending = row.kind === 'pending'

  return (
    <div className="flex items-start gap-3">
      <div className="min-w-0 flex-1 space-y-1.5">
        <span className="block truncate font-medium text-foreground">{row.title}</span>

        {/*  Số hiệu + bước duyệt trên một dòng phụ. Dấu `·` nằm CÙNG span với vế
             đứng sau nó — tách ra thành phần tử riêng thì lúc co chữ nó ở lại
             cuối dòng trên, thành một dấu chấm giữa mồ côi treo ở mép phải. */}
        <span className="flex min-w-0 items-center gap-1 text-xs text-muted-foreground">
          {row.code ? (
            <span className="truncate font-mono text-navy">{row.code}</span>
          ) : (
            <span className="shrink-0">Chưa cấp số</span>
          )}
          {row.nodeName && (
            <span className="truncate">
              <span aria-hidden="true">· </span>
              {row.nodeName}
            </span>
          )}
        </span>

        <div className="flex flex-wrap items-center gap-1.5">
          {pending ? (
            //  Quá hạn tô đỏ ngay ở huy hiệu, y như cột «Tình trạng» của bảng:
            //  mức gấp gáp không được phụ thuộc vào việc dòng hạn bên dưới có
            //  chỗ hiện hay không.
            <Badge variant={row.isOverdue ? 'destructive' : 'default'}>
              {row.isOverdue ? 'Quá hạn' : 'Cần duyệt'}
            </Badge>
          ) : (
            <Badge variant={ACTION_TONE[row.action ?? 0] ?? 'outline'}>{row.actionLabel}</Badge>
          )}
        </div>

        {pending
          ? (row.startedByName || row.dueAt) && (
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                {row.startedByName && (
                  <span className="flex min-w-0 items-center gap-1">
                    <UserRound className="size-3 shrink-0" aria-hidden="true" />
                    <span className="truncate">{row.startedByName}</span>
                  </span>
                )}
                {row.dueAt && (
                  <span
                    className={
                      row.isOverdue
                        ? 'flex items-center gap-1 font-medium text-destructive'
                        : 'flex items-center gap-1'
                    }
                  >
                    <Clock className="size-3 shrink-0" aria-hidden="true" />
                    <span className="tabular-nums">Hạn {formatDate(row.dueAt)}</span>
                  </span>
                )}
              </div>
            )
          : (row.decidedAt || row.instanceStatusLabel) && (
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                {row.decidedAt && (
                  <span className="tabular-nums">{formatDateTime(row.decidedAt)}</span>
                )}

                {/*  ⚠️ «Phiếu bây giờ» phải đi kèm CHỮ «Phiếu», không được là một
                     huy hiệu trần. Ở bảng nó là một cột có tiêu đề, chính tiêu đề
                     đó phân biệt nó với cột «Tình trạng» bên cạnh; thẻ không có
                     tiêu đề cột, nên hai huy hiệu đứng liền nhau đọc ra
                     «Duyệt · Đã duyệt» — hai chữ gần như đồng nghĩa, người đọc
                     không đoán được cái nào nói việc CỦA TÔI và cái nào nói cả
                     TỜ PHIẾU. Mà đó đúng là hai chuyện khác nhau: tôi ký xong
                     bước của mình không có nghĩa là phiếu đã xong. */}
                {row.instanceStatusLabel && <span>Phiếu: {row.instanceStatusLabel}</span>}
              </div>
            )}
      </div>

      {/*  Mũi tên nói THẺ NÀY BẤM ĐƯỢC: màn cảm ứng không có con trỏ đổi hình khi
           rê qua, nên phải nói bằng hình. */}
      <ChevronRight className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
    </div>
  )
}
