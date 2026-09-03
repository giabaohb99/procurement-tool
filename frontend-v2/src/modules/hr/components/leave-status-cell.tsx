import { MessageSquareWarning } from 'lucide-react'

import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/shared/ui/tooltip'
import type { LeaveRequest } from '../types/leave'
import { decisionNoteLabelOf, decisionNoteOf } from '../utils/leave-decision-note'
import { LeaveStatusBadge } from './leave-status-badge'

interface LeaveStatusCellProps {
  request: Pick<LeaveRequest, 'status' | 'status_label' | 'decision_note'>
}

/**
 * Ô TRẠNG THÁI của bảng đơn nghỉ phép: huy hiệu, và với ba kết cục xấu thì kèm
 * luôn lý do bị chặn.
 *
 * Vì sao kèm lý do: chỉ một chữ «Từ chối» đỏ thì người nộp phải mở từng đơn ra
 * mới biết mình sai chỗ nào, và câu hỏi đó đi vòng qua điện thoại tới phòng
 * Nhân sự.
 *
 * Ba điều kiện mà bản đầu (chữ đỏ trần trụi dán sát huy hiệu) đều hụt:
 *
 * 1. **Phải nói rõ đây là lý do của việc gì.** Cột «Lý do» (lý do NGHỈ) nằm
 *    ngay trong cùng bảng và cũng là chữ tự do — hai đoạn chữ tự do không nhãn
 *    thì không phân biệt được. Nên có biểu tượng ghi chú dẫn đầu, và tooltip mở
 *    ra bằng đúng nhãn «Lý do từ chối / trả về / hủy yêu cầu».
 * 2. **Không tô đỏ đoạn chữ.** Màu đỏ đã là việc của huy hiệu; đỏ thêm lần nữa
 *    ở một đoạn chữ 12px trông như lỗi hiển thị. Chữ phụ để màu mờ, đúng vai
 *    ghi chú.
 * 3. **Lý do dài không được làm vỡ gì cả.** `decision_note` chặn ở 500 ký tự và
 *    có thể là một chuỗi liền không dấu cách. Trong ô: `min-w-0` + `truncate`
 *    (thiếu `min-w-0` thì ô flex không co nhỏ hơn nội dung, cột bị nong ra và
 *    đẩy vỡ bảng). Trong tooltip: chặn bề ngang và bẻ dòng giữa từ, nếu không
 *    `w-fit` mặc định sẽ kéo khung tooltip dài hơn cả màn hình.
 */
export function LeaveStatusCell({ request }: LeaveStatusCellProps) {
  const note = decisionNoteOf(request)
  const label = decisionNoteLabelOf(request.status)

  return (
    <div className="flex min-w-0 items-center gap-2">
      <span className="shrink-0">
        <LeaveStatusBadge status={request.status} label={request.status_label} />
      </span>

      {note && (
        <TooltipProvider delayDuration={150}>
          <Tooltip>
            <TooltipTrigger asChild>
              <span
                className="inline-flex min-w-0 items-center gap-1 text-xs text-muted-foreground"
                aria-label={`${label}: ${note}`}
              >
                <MessageSquareWarning className="size-3.5 shrink-0" aria-hidden="true" />
                <span className="truncate">{note}</span>
              </span>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-80 break-words whitespace-pre-wrap">
              <span className="block font-semibold">{label}</span>
              {note}
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )}
    </div>
  )
}
