import { Check, Undo2, X } from 'lucide-react'
import { useState } from 'react'

import { useApprovalAction, useMyTasks } from '@/modules/approval/hooks/use-approvals'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import { ReasonConfirmDialog } from '@/shared/ui/reason-confirm-dialog'

type Decision = 'approve' | 'reject' | 'return'

const DIALOG: Record<Decision, { title: string; description: string; confirm: string }> = {
  approve: {
    title: 'Duyệt phiếu đặt phòng',
    description: 'Phòng sẽ thuộc về phiếu này trong khung giờ đã đặt, và người được mời nhận thông báo.',
    confirm: 'Duyệt phiếu',
  },
  reject: {
    title: 'Từ chối phiếu đặt phòng',
    description: 'Phòng được nhả ra ngay. Người đặt phải lập phiếu khác nếu vẫn cần họp.',
    confirm: 'Từ chối',
  },
  return: {
    title: 'Trả về để chỉnh sửa',
    description: 'Người đặt sửa lại rồi gửi duyệt lần nữa. Phòng được nhả trong lúc chờ họ sửa.',
    confirm: 'Trả về',
  },
}

/**
 * Ba nút quyết định trên TRANG CHI TIẾT — chỉ hiện khi phiếu đang chờ CHÍNH TÔI ký.
 *
 * ⚠️ **Điều kiện hiện nút là "có việc treo", không phải "có quyền approve"** —
 * cùng bài học với `LeaveDetailDecisionActions` (CR-260). Lẫn hai thứ đó là hỏng
 * theo cả hai chiều: người có khóa `room_booking.approve` nhưng không nằm trong
 * luồng thì bấm vào ăn lỗi, còn người được bộ máy giao ký nhưng không có khóa đó
 * thì mở phiếu ra chẳng thấy nút nào.
 *
 * Dùng thẳng hộp việc DÙNG CHUNG (`useMyTasks('room_booking')`) chứ không dựng
 * hộp việc riêng cho đặt phòng: bộ máy duyệt đã có sẵn hàng đợi đó, và mọi phiếu
 * chờ ký của người dùng đều nằm chung một chỗ ở màn Phê duyệt.
 */
export function RoomDecisionActions({ bookingId }: { bookingId: number }) {
  const { data: tasks } = useMyTasks('room_booking')
  const [decision, setDecision] = useState<Decision | null>(null)

  const task = tasks?.items.find((row) => row.entity_id === bookingId)
  const act = useApprovalAction(task?.instance_id ?? 0, 'room_booking')
  //  Chặn bấm trùng trong cùng một nhịp — `disabled={isPending}` chỉ bật ở lần
  //  render kế nên hai cú bấm liền tay ra hai lệnh ký. Xem `useSingleFlight`.
  const once = useSingleFlight()

  if (!task) return null

  return (
    <>
      <Button variant="outline" onClick={() => setDecision('return')} disabled={act.isPending}>
        <Undo2 className="size-4" />
        Trả về
      </Button>
      <Button
        variant="outline"
        className="text-destructive hover:text-destructive"
        onClick={() => setDecision('reject')}
        disabled={act.isPending}
      >
        <X className="size-4" />
        Từ chối
      </Button>
      <Button onClick={() => setDecision('approve')} disabled={act.isPending}>
        <Check className="size-4" />
        Duyệt phiếu
      </Button>

      <ReasonConfirmDialog
        open={decision !== null}
        onOpenChange={(open) => !open && setDecision(null)}
        title={DIALOG[decision ?? 'approve'].title}
        description={DIALOG[decision ?? 'approve'].description}
        placeholder={decision === 'approve' ? 'Ý kiến (không bắt buộc)' : 'Vì sao?'}
        confirmText={DIALOG[decision ?? 'approve'].confirm}
        //  Duyệt KHÔNG bắt buộc ghi lý do; hai việc kia thì có — người đặt cần
        //  biết phải sửa gì, hoặc vì sao bị từ chối.
        optional={decision === 'approve'}
        destructive={decision !== 'approve'}
        pending={act.isPending}
        onConfirm={(reason) => {
          if (!decision) return
          void once(async () => {
            await act.mutateAsync({ kind: decision, text: reason })
            //  Đóng hộp SAU khi gọi xong, không đóng ngay lúc bấm: gọi hỏng mà
            //  hộp đã đóng thì người dùng tưởng mình đã ký xong.
            setDecision(null)
          })
        }}
      />
    </>
  )
}
