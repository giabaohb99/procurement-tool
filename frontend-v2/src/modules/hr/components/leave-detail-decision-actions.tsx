import { Check, Undo2, X } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import {
  useLeaveApprovalDecision,
  useLeaveToApprove,
  type ApprovalDecision,
} from '../hooks/use-leave'
import {
  PRIMARY_ACTION_SLOT,
  SECONDARY_ACTION_SLOT,
} from '../utils/leave-detail-action-slots'
import { LeaveDecisionDialog } from './leave-decision-dialog'

interface LeaveDetailDecisionActionsProps {
  requestId: number
}

/**
 * Ba nút quyết định trên TRANG CHI TIẾT, chỉ hiện khi đơn đang chờ CHÍNH TÔI ký
 * (CR-260).
 *
 * ⚠️ **Điều kiện hiện nút là "có việc treo", không phải "có quyền approve".**
 * Hai thứ đó khác nhau và lẫn lộn là hỏng theo cả hai chiều: người có khóa
 * `leave_request.approve` nhưng không nằm trong luồng sẽ thấy nút rồi bấm vào
 * ăn *"bạn không có việc nào đang chờ ở phiếu này"*; ngược lại, Trưởng phòng
 * Nhân sự được bộ máy giao ký nhưng không được cấp khóa đó thì mở đơn ra chẳng
 * thấy nút nào.
 *
 * Dùng lại đúng hàng đợi của tab «Cần tôi duyệt» chứ không gọi riêng: người
 * dùng thường vào đây TỪ tab đó, nên dữ liệu đã nằm sẵn trong cache và không
 * tốn thêm lượt gọi nào.
 */
export function LeaveDetailDecisionActions({ requestId }: LeaveDetailDecisionActionsProps) {
  const { data } = useLeaveToApprove(requestId > 0)
  const decide = useLeaveApprovalDecision()
  const [decision, setDecision] = useState<ApprovalDecision | null>(null)

  const row = data?.items.find((item) => item.id === requestId)
  if (!row) return null

  return (
    <>
      <Button
        variant="outline"
        className={SECONDARY_ACTION_SLOT}
        onClick={() => setDecision('return')}
        disabled={decide.isPending}
      >
        <Undo2 className="size-4" />
        Trả về
      </Button>
      <Button
        variant="outline"
        className={cn('text-destructive hover:text-destructive', SECONDARY_ACTION_SLOT)}
        onClick={() => setDecision('reject')}
        disabled={decide.isPending}
      >
        <X className="size-4" />
        Từ chối
      </Button>
      {/*  Duyệt là việc người mở màn này định làm — nút CHÍNH, xem
           `leave-detail-action-slots.ts`. */}
      <Button
        className={PRIMARY_ACTION_SLOT}
        onClick={() => setDecision('approve')}
        disabled={decide.isPending}
      >
        <Check className="size-4" />
        Duyệt đơn
      </Button>

      <LeaveDecisionDialog
        row={decision ? row : null}
        decision={decision ?? 'approve'}
        isPending={decide.isPending}
        onClose={() => setDecision(null)}
        onConfirm={(reason) => {
          if (!decision) return
          decide.mutate(
            { instanceId: row.task.instance_id, decision, reason },
            //  Đóng hộp trong `onSuccess`, không đóng ngay lúc bấm: gọi hỏng mà
            //  hộp đã đóng thì người dùng tưởng mình đã ký xong.
            { onSuccess: () => setDecision(null) },
          )
        }}
      />
    </>
  )
}
