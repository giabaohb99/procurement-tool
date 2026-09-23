import { useQuery } from '@tanstack/react-query'

import { approvalApi } from '@/modules/approval/api/approval-api'
import { useMyTasks } from '@/modules/approval/hooks/use-approvals'
import { INSTANCE_STATUS } from '@/modules/approval/types/approval'
import { queryKeys } from '@/shared/constants/query-keys'

const ENTITY = 'vehicle_booking'

/**
 * LƯỢT KÝ CỦA TÔI trên một phiếu đặt xe đang chạy luồng duyệt nhiều bước —
 * `undefined` khi không tới lượt (hoặc phiếu không ở trong luồng nào).
 *
 * Hỏi cả phiên duyệt chứ không chỉ danh sách việc: phiên đã đóng mà danh sách
 * việc chưa kịp nạp lại thì nút duyệt sẽ sống thêm một nhịp và bấm vào ra lỗi.
 *
 * `enabled = false` thì KHÔNG gọi gì cả. Cụm nút của phiếu đặt xe được dựng trên
 * từng thẻ ở màn «Chuyến của tôi», nên không gác là mỗi thẻ một lượt hỏi bộ máy
 * duyệt — dù chỉ phiếu đang chạy luồng mới cần biết.
 */
export function useMyBookingApprovalTask(bookingId: number, enabled = true) {
  const active = enabled && bookingId > 0
  const { data: instance } = useQuery({
    queryKey: queryKeys.approval.ofEntity(ENTITY, bookingId),
    queryFn: () => approvalApi.ofEntity(ENTITY, bookingId),
    enabled: active,
  })
  const { data: tasks } = useMyTasks(undefined, active)

  if (!active || instance?.status !== INSTANCE_STATUS.running) return undefined
  return (tasks?.items ?? []).find((t) => t.entity === ENTITY && t.entity_id === bookingId)
}
