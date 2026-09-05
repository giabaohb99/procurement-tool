import { useQuery } from '@tanstack/react-query'
import { GitBranch, ShieldCheck } from 'lucide-react'
import { useState } from 'react'

import { approvalApi } from '@/modules/approval/api/approval-api'
import { ApprovalActionDialog } from '@/modules/approval/components/approval-action-dialog'
import { ApprovalTrailCard } from '@/modules/approval/components/approval-trail-card'
import { INSTANCE_STATUS } from '@/modules/approval/types/approval'
import { useMyTasks } from '@/modules/approval/hooks/use-approvals'
import { queryKeys } from '@/shared/constants/query-keys'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'

const ENTITY = 'vehicle_booking'

/**
 * Bảng LUỒNG DUYỆT NHIỀU BƯỚC của một phiếu đặt xe — chỉ hiện khi phiếu thật sự
 * có một phiên duyệt (bật `ApprovalSwitch` + có luồng khớp). Tái dùng nguyên bộ
 * máy chung: `ofEntity` lấy phiên, `useMyTasks` tìm lượt của tôi, `ApprovalActionDialog`
 * để Duyệt/Trả/Từ chối, `ApprovalTrailCard` xem dấu vết. Không có phiên → không vẽ gì
 * (phiếu chạy đường duyệt một bước cũ).
 */
export function BookingApprovalPanel({ bookingId }: { bookingId: number }) {
  const { data: instance } = useQuery({
    queryKey: queryKeys.approval.ofEntity(ENTITY, bookingId),
    queryFn: () => approvalApi.ofEntity(ENTITY, bookingId),
    enabled: bookingId > 0,
  })
  const { data: tasks } = useMyTasks()
  const [actOpen, setActOpen] = useState(false)

  if (!instance) return null

  const running = instance.status === INSTANCE_STATUS.running
  const myTask = (tasks?.items ?? []).find(
    (t) => t.entity === ENTITY && t.entity_id === bookingId,
  )

  return (
    <Card className="flex flex-col gap-3 p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          <GitBranch className="size-4" />
          Luồng duyệt nhiều bước
        </h3>
        <Badge variant={running ? 'secondary' : 'outline'}>{instance.status_label}</Badge>
      </div>

      <p className="text-sm text-muted-foreground">
        Luồng «{instance.flow_name}»
        {running && <> — đang ở bước {instance.current_seq}</>}.
      </p>

      {running &&
        (myTask ? (
          <div>
            <Button onClick={() => setActOpen(true)}>
              <ShieldCheck className="size-4" />
              Xử lý duyệt
            </Button>
          </div>
        ) : (
          <p className="rounded-md bg-accent px-3 py-2 text-[13px] text-muted-foreground">
            Đang chờ người duyệt của bước hiện tại. Bạn sẽ xử lý ở đây khi tới lượt.
          </p>
        ))}

      <ApprovalTrailCard instanceId={instance.id} />

      {myTask && (
        <ApprovalActionDialog task={myTask} open={actOpen} onOpenChange={setActOpen} />
      )}
    </Card>
  )
}
