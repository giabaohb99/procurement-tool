import { Check, CircleDashed, CircleDot, MinusCircle, X } from 'lucide-react'

import { ApprovalTrailCard } from '@/modules/approval/components/approval-trail-card'
import { INSTANCE_STATUS, TASK_STATUS } from '@/modules/approval/types/approval'
import type { ApprovalInstance, ApprovalTask } from '@/modules/approval/types/approval'
import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { cn } from '@/shared/utils/cn'

interface DocumentApprovalTabProps {
  instance: ApprovalInstance | null | undefined
}

/** Bộ mặt của một chặng, gộp từ trạng thái các việc thuộc chặng đó. */
function trangThaiChang(viec: ApprovalTask[], seq: number, instance: ApprovalInstance) {
  const cua = viec.filter((row) => row.node_seq === seq)
  if (cua.some((row) => row.status === TASK_STATUS.rejected)) return 'tu-choi'
  if (cua.some((row) => row.status === TASK_STATUS.pending)) return 'dang-cho'
  if (cua.length > 0 && cua.every((row) => row.status === TASK_STATUS.skippedDuplicate))
    return 'tu-qua'
  if (cua.some((row) => row.status === TASK_STATUS.approved)) return 'xong'
  //  Chưa có việc nào ở chặng này: hoặc chưa tới lượt, hoặc phiếu đã dừng trước
  //  khi tới đây. Cả hai đều vẽ như nhau — chặng chưa chạm tới.
  return instance.current_seq > seq ? 'khong-chay' : 'chua-toi'
}

const HINH = {
  xong: { icon: Check, mau: 'text-emerald-600', nhan: 'Đã duyệt' },
  'dang-cho': { icon: CircleDot, mau: 'text-primary', nhan: 'Đang chờ' },
  'tu-choi': { icon: X, mau: 'text-destructive', nhan: 'Từ chối' },
  'tu-qua': { icon: MinusCircle, mau: 'text-muted-foreground', nhan: 'Tự qua vì trùng người' },
  'chua-toi': { icon: CircleDashed, mau: 'text-muted-foreground', nhan: 'Chưa tới lượt' },
  'khong-chay': { icon: CircleDashed, mau: 'text-muted-foreground', nhan: 'Không chạy' },
} as const

/**
 * Tab PHÊ DUYỆT của trang chi tiết văn bản: phiếu này đang đi tới đâu.
 *
 * Trang chi tiết trước đây không nói gì về luồng duyệt ngoài hai chữ «Đang
 * duyệt», nên người soạn không biết chờ ai còn người vừa ký không biết mình
 * đang đứng ở khúc nào của một luồng bốn bước.
 *
 * Hai kiểu bước dễ đọc nhầm nên phải phân biệt bằng mắt:
 *
 * - **nhiều người trong CÙNG một chặng** — mỗi người một dòng con, thấy ngay còn
 *   thiếu chữ ký nào;
 * - **tự qua vì trùng người duyệt** — KHÁC "đã duyệt", vẽ mờ và nói rõ, vì gộp
 *   làm một là bản in nói dối rằng có thêm một người đã xem xét.
 *
 * Không có nút bấm nào ở đây: duyệt là việc làm ở «Việc của tôi», nơi bộ máy
 * biết ai đang cầm việc. Bày nút ở đây lại đẻ ra đúng cái đường tắt vừa bịt.
 */
export function DocumentApprovalTab({ instance }: DocumentApprovalTabProps) {
  if (!instance) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-sm text-muted-foreground">
          Văn bản này chưa vào bộ máy duyệt nhiều bước.
          <br />
          Nó đi theo luồng duyệt một bước cũ, hoặc chưa được gửi duyệt lần nào.
        </CardContent>
      </Card>
    )
  }

  const viec = instance.tasks ?? []
  const chang = [...new Set((instance.steps ?? []).map((buoc) => buoc.seq))].sort((a, b) => a - b)

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="text-base">
            Luồng «{instance.flow_name}» bản {instance.flow_version}
          </CardTitle>
          <Badge
            variant={
              instance.status === INSTANCE_STATUS.approved
                ? 'default'
                : instance.status === INSTANCE_STATUS.blocked ||
                    instance.status === INSTANCE_STATUS.rejected
                  ? 'destructive'
                  : 'outline'
            }
          >
            {instance.status_label}
          </Badge>
        </CardHeader>

        <CardContent>
          <ol className="space-y-3">
            {chang.map((seq) => {
              const ten =
                (instance.steps ?? []).find((buoc) => buoc.seq === seq)?.name || `Bước ${seq}`
              const trang_thai = trangThaiChang(viec, seq, instance)
              const { icon: Icon, mau, nhan } = HINH[trang_thai]
              const nguoi = viec.filter((row) => row.node_seq === seq)

              return (
                <li key={seq} className="flex gap-3">
                  <Icon className={cn('mt-0.5 size-4 shrink-0', mau)} />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium">
                      Chặng {seq} · {ten}
                      <span className="ml-2 font-normal text-muted-foreground">{nhan}</span>
                    </p>
                    {nguoi.length > 0 && (
                      <ul className="mt-0.5 space-y-0.5">
                        {nguoi.map((row) => (
                          <li key={row.id} className="text-sm text-muted-foreground">
                            {row.assignee_name} — {row.status_label}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </li>
              )
            })}
          </ol>
        </CardContent>
      </Card>

      <ApprovalTrailCard instanceId={instance.id} />
    </div>
  )
}
