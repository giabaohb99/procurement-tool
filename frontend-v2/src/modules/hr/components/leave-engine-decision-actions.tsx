import { Check, Undo2, X } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { ReasonConfirmDialog } from '@/shared/ui/reason-confirm-dialog'
import { cn } from '@/shared/utils/cn'
import { useLeaveApprovalDecision, type ApprovalDecision } from '../hooks/use-leave'
import { useSingleFlight } from '../hooks/use-single-flight'
import { PRIMARY_ACTION_SLOT, SECONDARY_ACTION_SLOT } from '../utils/leave-detail-action-slots'

/** Chữ của hộp xác nhận cho từng quyết định — mỗi loại phiếu tự khai. */
export interface EngineDecisionFace {
  title: string
  description: string
  placeholder: string
  confirm: string
  /** Lý do không bắt buộc (thường chỉ khi Duyệt). */
  optional: boolean
}

interface LeaveEngineDecisionActionsProps {
  /** Phiên duyệt chứa việc treo của TÔI; vắng = tôi không có việc gì trên phiếu này → không dựng nút. */
  instanceId?: number
  faces: Record<ApprovalDecision, EngineDecisionFace>
  /** Nhãn nút Duyệt (vd "Duyệt phiếu"). */
  approveLabel?: string
  /** Khóa truy vấn của phân hệ khác cần làm mới sau khi ký (vd `queryKeys.finance.all`). */
  alsoInvalidate?: readonly (readonly unknown[])[]
}

/**
 * Ba nút duyệt qua BỘ MÁY (Duyệt · Trả về · Từ chối) dùng chung cho các phiếu của cụm Nghỉ phép (nghỉ bù, thanh toán
 * nghỉ phép). Ký theo PHIÊN (`useLeaveApprovalDecision` → `/api/approvals/{instance}/...`), không gắn với loại phiếu.
 *
 * ⚠️ Điều kiện hiện nút là "có việc treo của TÔI" (nơi gọi đọc từ `/to-approve` rồi truyền `instanceId`), không phải
 * "có quyền approve". Chặn bấm đúp "Xác nhận" bằng `useSingleFlight` (isPending đổi chậm một nhịp).
 */
export function LeaveEngineDecisionActions({
  instanceId,
  faces,
  approveLabel = 'Duyệt phiếu',
  alsoInvalidate,
}: LeaveEngineDecisionActionsProps) {
  const decide = useLeaveApprovalDecision({ alsoInvalidate })
  const [decision, setDecision] = useState<ApprovalDecision | null>(null)
  const runOnce = useSingleFlight()

  if (!instanceId) return null
  const face = faces[decision ?? 'approve']

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
        {approveLabel}
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
              { instanceId, decision, reason },
              { onSuccess: () => setDecision(null), onSettled: release },
            ),
          )
        }}
      />
    </>
  )
}
