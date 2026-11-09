import { queryKeys } from '@/shared/constants/query-keys'
import type { ApprovalDecision } from '../hooks/use-leave'
import { useLeaveEncashmentToApprove } from '../hooks/use-leave-encashment'
import { LeaveEngineDecisionActions, type EngineDecisionFace } from './leave-engine-decision-actions'

interface LeaveEncashmentDecisionActionsProps {
  requestId: number
}

const FACES: Record<ApprovalDecision, EngineDecisionFace> = {
  approve: {
    title: 'Duyệt phiếu thanh toán nghỉ phép',
    description:
      'Duyệt xong chặng cuối: số ngày bị trừ khỏi quỹ phép và kế toán nhận một yêu cầu thanh toán để nhập số tiền.',
    placeholder: 'Ý kiến (không bắt buộc)',
    confirm: 'Duyệt',
    optional: true,
  },
  return: {
    title: 'Trả phiếu về chỉnh sửa',
    description: 'Người lập sẽ đọc đúng câu này để biết phải sửa gì. Số ngày đang giữ chỗ được trả lại quỹ.',
    placeholder: 'Cần sửa gì?',
    confirm: 'Trả về',
    optional: false,
  },
  reject: {
    title: 'Từ chối phiếu thanh toán nghỉ phép',
    description: 'Phiếu dừng lại, số ngày đang giữ chỗ được trả lại quỹ phép.',
    placeholder: 'Vì sao không duyệt?',
    confirm: 'Từ chối',
    optional: false,
  },
}

/** Ba nút duyệt qua BỘ MÁY trên trang chi tiết phiếu thanh toán nghỉ phép (chỉ khi tôi có việc treo trên phiếu). */
export function LeaveEncashmentDecisionActions({ requestId }: LeaveEncashmentDecisionActionsProps) {
  const { data } = useLeaveEncashmentToApprove(requestId > 0)
  const row = data?.items.find((item) => item.id === requestId)
  //  Duyệt chặng cuối sinh YCTT bên Tài chính: làm mới cả nhánh `finance` để danh sách YCTT thấy phiếu mới.
  return (
    <LeaveEngineDecisionActions
      instanceId={row?.task.instance_id}
      faces={FACES}
      alsoInvalidate={[queryKeys.finance.all]}
    />
  )
}
