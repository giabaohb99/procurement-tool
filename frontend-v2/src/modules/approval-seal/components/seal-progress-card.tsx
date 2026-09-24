import { BadgeCheck } from 'lucide-react'

import { useAuditLogs } from '@/shared/audit'
import { Card } from '@/shared/ui/card'
import { TimelineItem, TimelineMarker } from '@/shared/ui/timeline-item'
import { cn } from '@/shared/utils/cn'
import type { SealRequest } from '../types/seal-request'
import { buildSealStages, type SealStage } from '../utils/build-seal-stages'
import { extractSealStopReason } from '../utils/extract-seal-reason'
import { SealSectionHeader } from './seal-section-header'

/**
 * Thẻ **TIẾN TRÌNH DUYỆT & ĐÓNG DẤU** — Lập phiếu → TBP duyệt → Văn thư đóng dấu,
 * xếp trên một trục dọc (22/09/2026, thay thẻ bốn dòng «Thông tin phê duyệt &
 * Đóng dấu»).
 *
 * Thẻ cũ bày bốn ô nhãn-trái/giá-trị-phải; phiếu mới thì cả bốn là dấu gạch, và
 * người LẬP phiếu — mắt xích đầu tiên — không có mặt ở đâu cả. Ở đây chặng chưa
 * tới lượt vẫn hiện, nhưng hiện thành một CÂU («Chờ Trưởng bộ phận duyệt») với
 * vòng tròn nét đứt, nên nhìn phát biết phiếu đang dừng ở đâu và còn ai phải ký.
 *
 * Luật chặng nằm ở `utils/build-seal-stages.ts` (hàm thuần, có bài kiểm). Khuôn
 * trục dọc dùng chung với phân hệ Đặt xe (`shared/ui/timeline-item.tsx`).
 */
export function SealProgressCard({
  request,
  editing = false,
}: {
  request: SealRequest
  /** Đang mở biểu mẫu sửa — xem chú thích `editing` ở `buildSealStages`. */
  editing?: boolean
}) {
  //  ⚠️ Lý do bị từ chối / trả về KHÔNG có cột riêng trên phiếu — nó nằm trong câu
  //  nhật ký (xem `extract-seal-reason.ts`). Lượt gọi này KHÔNG tốn thêm request:
  //  màn chi tiết đã dựng `AuditTimeline` với đúng khóa truy vấn
  //  `['audit-logs', entity, id]`, TanStack Query dùng lại cache.
  const { data: auditEntries } = useAuditLogs('seal_request', request.id)
  const stopReason = extractSealStopReason(auditEntries)?.reason ?? ''

  const stages = buildSealStages(request, { editing, stopReason })

  return (
    <Card className="flex flex-col gap-4 p-5 pb-4">
      <SealSectionHeader
        icon={BadgeCheck}
        title="Tiến trình duyệt & Đóng dấu"
        iconColor="text-emerald-600 dark:text-emerald-400"
      />

      <ol className="flex flex-col">
        {stages.map((stage, index) => (
          <TimelineItem
            key={stage.key}
            last={index === stages.length - 1}
            marker={<TimelineMarker state={stage.state} />}
          >
            <StageRow stage={stage} />
          </TimelineItem>
        ))}
      </ol>
    </Card>
  )
}

/**
 * Một chặng: TÊN CHẶNG một dòng, người + mốc giờ xuống dòng dưới.
 *
 * Xếp cả ba thứ trên một dòng chỉ đẹp ở cột rộng; thẻ này sống ở CỘT PHỤ 380px,
 * ở đó «Chờ Trưởng bộ phận duyệt · Trần Trưởng Phòng · 17/09/2026 11:42» gãy
 * dòng tùy tiện và tên chặng — thứ duy nhất cần liếc là thấy — chìm giữa hai mẩu
 * chữ xám.
 */
function StageRow({ stage }: { stage: SealStage }) {
  const muted = stage.state === 'pending'

  return (
    <div className="-mt-0.5 flex flex-col gap-0.5">
      <span
        className={cn(
          'text-sm font-medium',
          stage.state === 'stopped' && 'text-destructive',
          muted && 'text-muted-foreground',
        )}
      >
        {stage.title}
      </span>

      {stage.actor && (
        <span className="text-xs text-muted-foreground">
          {stage.actorLabel && `${stage.actorLabel}: `}
          <span className="font-medium text-foreground">{stage.actor}</span>
        </span>
      )}

      {stage.time && <span className="text-xs tabular-nums text-muted-foreground">{stage.time}</span>}

      {/*  ⚠️ Lý do là CHỮ THƯỜNG, cùng nhịp với dòng «Người xử lý» ngay trên nó.
          Bản trước đóng khung đỏ nhạt (viền + nền) — trong một cột hẹp nó đọc ra
          như một hộp cảnh báo của hệ thống chứ không ra lời người duyệt viết, mà
          chặng đã có vòng tròn đỏ + tiêu đề đỏ rồi, thêm mảng đỏ thứ ba là thừa.
          Nhãn xám, nội dung chữ thường: khác nhau đủ để tách, không hét lên. */}
      {stage.reason && (
        <p className="text-xs leading-relaxed whitespace-pre-wrap text-muted-foreground">
          Lý do: <span className="text-foreground">{stage.reason}</span>
        </p>
      )}
    </div>
  )
}
