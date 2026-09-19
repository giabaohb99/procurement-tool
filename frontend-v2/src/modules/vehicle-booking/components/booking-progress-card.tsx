import { BadgeCheck, Check, X } from 'lucide-react'
import type { ReactNode } from 'react'

import { Card } from '@/shared/ui/card'
import { cn } from '@/shared/utils/cn'
import type { VehicleBooking } from '../types/vehicle-booking'
import { buildBookingStages, type BookingStage } from '../utils/build-booking-stages'
import { BookingCardHeader } from './booking-info-item'
import { TimelineItem } from './booking-timeline-item'
import { DriverStatusBadge } from './status-pill'

/**
 * Thẻ TIẾN TRÌNH XỬ LÝ — Tạo phiếu → Phê duyệt → Điều phối → Hoàn thành.
 *
 * Thay cho khối "Thông tin phê duyệt" cũ: mười ô có viền nằm cạnh nhau, phiếu
 * mới thì cả mười đều trống. Ở đây chặng chưa tới lượt vẫn hiện, nhưng hiện
 * thành một CÂU ("Chờ điều phối") với vòng tròn nét đứt — người đọc biết ngay
 * phiếu đang dừng ở đâu thay vì phải suy ra từ những ô trống.
 *
 * Luật chặng nằm ở `utils/build-booking-stages.ts` (hàm thuần, có bài kiểm).
 */
export function BookingProgressCard({ booking }: { booking: VehicleBooking }) {
  const stages = buildBookingStages(booking)

  return (
    //  Cỡ lề khớp hai thẻ hàng xóm ở cột phụ (`DocumentComments`, `AuditTimeline`):
    //  `py-4 px-4` + tiêu đề `text-base`, không phải `p-5` như thẻ ở cột chính.
    <Card className="flex flex-col gap-4 p-4 pb-3">
      <BookingCardHeader
        className="-mx-4 px-4 text-base"
        icon={<BadgeCheck className="size-5 text-emerald-600 dark:text-emerald-400" />}
      >
        Tiến trình xử lý
      </BookingCardHeader>

      <ol className="flex flex-col">
        {stages.map((stage, index) => (
          <TimelineItem
            key={stage.key}
            last={index === stages.length - 1}
            marker={<StageMarker state={stage.state} />}
          >
            <StageRow
              stage={stage}
              //  Trạng thái tài xế thuộc chặng điều phối và CHỈ có nghĩa khi đã
              //  có tài xế — phiếu tự lái hay chưa phân xe thì badge rỗng.
              badge={
                stage.key === 'dispatch' && booking.assigned_driver_label ? (
                  <DriverStatusBadge
                    status={booking.driver_status}
                    label={booking.driver_status_label}
                  />
                ) : null
              }
            />
          </TimelineItem>
        ))}
      </ol>
    </Card>
  )
}

/**
 * Một chặng: TÊN CHẶNG đứng riêng một dòng, người + mốc giờ xuống dòng dưới.
 *
 * Xếp cả ba thứ trên một dòng (bản đầu) chỉ đẹp ở cột rộng; thẻ này sống ở CỘT
 * PHỤ 360px, ở đó "Đã bố trí xe (tự lái) · Trần Minh Được · 15/09/2026 04:56"
 * gãy dòng tùy tiện và tên chặng — thứ duy nhất cần liếc là thấy — bị chìm giữa
 * hai mẩu chữ xám.
 */
function StageRow({ stage, badge }: { stage: BookingStage; badge?: ReactNode }) {
  const muted = stage.state === 'pending'
  const meta = [stage.actor, stage.time].filter(Boolean).join(' · ')

  return (
    <div className="-mt-0.5 flex flex-col gap-0.5">
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
        <span
          className={cn(
            'text-sm font-medium',
            stage.state === 'stopped' && 'text-destructive',
            muted && 'text-muted-foreground',
          )}
        >
          {stage.title}
        </span>
        {badge}
      </div>
      {meta && <span className="text-xs tabular-nums text-muted-foreground">{meta}</span>}
      {stage.facts.length > 0 && (
        <dl className="mt-0.5 flex flex-col gap-0.5">
          {stage.facts.map((fact) => (
            <div key={fact.label} className="flex min-w-0 items-baseline gap-1.5 text-xs">
              <dt className="shrink-0 text-muted-foreground">{fact.label}</dt>
              <dd className="min-w-0 break-words font-medium text-foreground">{fact.value}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  )
}

/** Vòng tròn đầu chặng: xong (đặc, dấu tick) · chờ (nét đứt) · dừng (đỏ, dấu X). */
function StageMarker({ state }: { state: BookingStage['state'] }) {
  if (state === 'done') {
    return (
      <span className="grid size-5 shrink-0 place-items-center rounded-full bg-emerald-500 text-white">
        <Check className="size-3" strokeWidth={3} />
      </span>
    )
  }
  if (state === 'stopped') {
    return (
      <span className="grid size-5 shrink-0 place-items-center rounded-full bg-destructive text-white">
        <X className="size-3" strokeWidth={3} />
      </span>
    )
  }
  return (
    <span
      className="size-5 shrink-0 rounded-full border-2 border-dashed border-muted-foreground/40"
      aria-hidden="true"
    />
  )
}
