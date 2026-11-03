import { Check, Undo2, X } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { ReasonConfirmDialog } from '@/shared/ui/reason-confirm-dialog'
import { cn } from '@/shared/utils/cn'
import { useLeaveCompToApprove } from '../hooks/use-leave-comp'
import { useLeaveApprovalDecision, type ApprovalDecision } from '../hooks/use-leave'
import { useSingleFlight } from '../hooks/use-single-flight'
import { PRIMARY_ACTION_SLOT, SECONDARY_ACTION_SLOT } from '../utils/leave-detail-action-slots'

interface LeaveCompDecisionActionsProps {
  requestId: number
}

const FACES: Record<
  ApprovalDecision,
  { title: string; description: string; placeholder: string; confirm: string; optional: boolean }
> = {
  approve: {
    title: 'Duyệt phiếu nghỉ bù',
    description: 'Duyệt xong, số ngày được cộng thêm vào quỹ phép của người nghỉ (nếu hết các chặng).',
    placeholder: 'Ý kiến (không bắt buộc)',
    confirm: 'Duyệt',
    optional: true,
  },
  return: {
    title: 'Trả phiếu về chỉnh sửa',
    description: 'Người lập sẽ đọc đúng câu này để biết phải sửa gì.',
    placeholder: 'Cần sửa gì?',
    confirm: 'Trả về',
    optional: false,
  },
  reject: {
    title: 'Từ chối phiếu nghỉ bù',
    description: 'Phiếu dừng lại, quỹ phép không đổi.',
    placeholder: 'Vì sao không duyệt?',
    confirm: 'Từ chối',
    optional: false,
  },
}

/**
 * Ba nút duyệt qua BỘ MÁY (Duyệt · Trả về · Từ chối) trên trang chi tiết phiếu nghỉ bù.
 *
 * ⚠️ Điều kiện hiện nút là «có việc treo của TÔI trên phiếu này» (đọc từ `/to-approve`), không phải
 * «có quyền approve» — cùng luật với `LeaveDetailDecisionActions`. Dùng chung hook ký theo PHIÊN
 * (`useLeaveApprovalDecision`): nó chỉ gọi `/api/approvals/{instance}/...` nên không gắn với nghỉ phép.
 */
export function LeaveCompDecisionActions({ requestId }: LeaveCompDecisionActionsProps) {
  const { data } = useLeaveCompToApprove(requestId > 0)
  const decide = useLeaveApprovalDecision()
  const [decision, setDecision] = useState<ApprovalDecision | null>(null)
  const runOnce = useSingleFlight()     // chặn bấm đúp «Xác nhận» (isPending đổi chậm một nhịp)

  const row = data?.items.find((item) => item.id === requestId)
  if (!row) return null
  const face = FACES[decision ?? 'approve']

  return (
    <>
      <Button
        type="button"
        variant="outline"
        className={SECONDARY_ACTION_SLOT}
        onClick={() => setDecision('return')}
        disabled={decide.isPending}
      >
        <Undo2 className="size-4" />
        Trả về
      </Button>
      <Button
        type="button"
        variant="outline"
        className={cn('text-destructive hover:text-destructive', SECONDARY_ACTION_SLOT)}
        onClick={() => setDecision('reject')}
        disabled={decide.isPending}
      >
        <X className="size-4" />
        Từ chối
      </Button>
      <Button
        type="button"
        className={PRIMARY_ACTION_SLOT}
        onClick={() => setDecision('approve')}
        disabled={decide.isPending}
      >
        <Check className="size-4" />
        Duyệt phiếu
      </Button>

      <ReasonConfirmDialog
        open={decision !== null}
        onOpenChange={(open) => !open && setDecision(null)}
        title={face.title}
        description={face.description}
        placeholder={face.placeholder}
        confirmText={face.confirm}
        optional={face.optional}
        destructive={decision === 'reject'}
        pending={decide.isPending}
        onConfirm={(reason) => {
          if (!decision) return
          runOnce((release) =>
            decide.mutate(
              { instanceId: row.task.instance_id, decision, reason },
              { onSuccess: () => setDecision(null), onSettled: release },
            ),
          )
        }}
      />
    </>
  )
}
