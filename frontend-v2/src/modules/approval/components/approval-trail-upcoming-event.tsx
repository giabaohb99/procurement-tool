import { ListTodo } from 'lucide-react'

import type { ApprovalUpcomingStage } from '../types/approval'

interface ApprovalTrailUpcomingEventProps {
  stages: ApprovalUpcomingStage[]
  showRail: boolean
}

/**
 * Mốc "CHẶNG TIẾP THEO (dự kiến)" ở đầu dòng thời gian — ai sẽ duyệt sau người
 * đang giữ việc.
 *
 * Danh sách đọc mới nhất trước, nên tương lai nằm TRÊN mốc "Đang chờ phản hồi".
 * Vòng mốc viền đứt để tách khỏi những mốc đã xảy ra: tên ở đây là kết quả tính
 * theo luồng tại thời điểm xem, còn đổi được tới lúc chặng mở thật.
 */
export function ApprovalTrailUpcomingEvent({ stages, showRail }: ApprovalTrailUpcomingEventProps) {
  return (
    <li className="relative flex gap-4 pb-7 last:pb-0">
      {showRail && (
        <span
          data-testid="approval-timeline-rail"
          aria-hidden="true"
          className="approval-timeline-rail print:bg-slate-400"
        />
      )}
      <span
        className="relative z-10 grid size-8 shrink-0 place-items-center rounded-full border border-dashed border-border bg-background text-muted-foreground print:bg-background"
        aria-hidden="true"
      >
        <ListTodo className="size-4" strokeWidth={2.25} />
      </span>

      <section className="min-w-0 flex-1 pt-1" aria-label="Chặng tiếp theo">
        <h4 className="text-sm font-semibold">
          Chặng tiếp theo <span className="font-normal text-muted-foreground">(dự kiến)</span>
        </h4>
        <ul className="mt-1 max-w-3xl space-y-1.5">
          {stages.map((stage) => (
            //  `break-words`: tên người và tên chặng là chữ tự do, chuỗi liền là tràn thẻ.
            <li key={stage.seq} className="text-sm leading-5 break-words text-muted-foreground">
              <span className="font-medium text-foreground">{approverText(stage)}</span>
              <span aria-hidden="true"> · </span>
              <span>Chặng {stage.seq}</span>
              {stage.name && `: ${stage.name}`}
              {stage.approvers.length === 0 && stage.unresolved_reason && (
                <p className="text-xs text-destructive">{stage.unresolved_reason}</p>
              )}
              {stage.note && <p className="text-xs">{stage.note}</p>}
            </li>
          ))}
        </ul>
      </section>
    </li>
  )
}

/**
 * Tên người duyệt dự kiến của một chặng. Chặng không ra ai thì nói thẳng: hoặc
 * chặng tự qua vì trùng người (có `note`), hoặc chưa tìm được người duyệt.
 */
function approverText(stage: ApprovalUpcomingStage): string {
  if (stage.approvers.length === 0) {
    return stage.note && !stage.unresolved_reason ? 'Tự động qua' : 'Chưa xác định người duyệt'
  }
  //  Người dự phòng không cần đuôi riêng: backend đã gửi kèm `note` nói rõ chuyện đó.
  return stage.approvers.map((row) => row.name).join(', ')
}
