import { Milestone } from 'lucide-react'

import { cn } from '@/shared/utils/cn'

interface ApprovalStageNoteProps {
  /** Câu tóm tắt do backend dựng (`approval_summary`) — ví dụ «Đang ở chặng 3/3 · Duyệt Brand & Pháp chế». */
  summary?: string | null
  className?: string
}

/**
 * Dòng phụ ĐI KÈM badge trạng thái: phiếu đang nằm ở chặng nào của luồng duyệt.
 *
 * Badge trạng thái chỉ trả lời «phiếu đã duyệt xong chưa», nên một phiếu đã qua
 * hai trong ba chặng vẫn hiện đúng một chữ *Chờ duyệt*. Với phiếu đồng bộ từ app
 * đặt xe cũ, người duyệt bấm bên app cũ và app cũ lại đặt tên trạng thái theo
 * CHẶNG đang chờ, nên hai màn hình đọc ra hai chuyện khác nhau về cùng một phiếu
 * (DD000864, 19/09/2026 — app cũ ghi «Đã Duyệt» trong khi phiếu còn chờ Pháp chế).
 * Dòng này lấp đúng chỗ hở đó mà KHÔNG đụng vào mã trạng thái.
 *
 * ⚠️ Câu chữ dựng ở backend (`approval/steps_service._summary`) để mọi màn nói
 * cùng một câu — đừng ghép lại từ `current_seq` ở đây.
 */
export function ApprovalStageNote({ summary, className }: ApprovalStageNoteProps) {
  const text = summary?.trim()
  if (!text) return null

  return (
    <span
      className={cn(
        'inline-flex min-w-0 items-center gap-1 text-[11px] text-muted-foreground',
        className,
      )}
      title={text}
    >
      <Milestone className="size-3 shrink-0" />
      <span className="truncate">{text}</span>
    </span>
  )
}
