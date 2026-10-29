import type { HeadcountPlanComputed, HeadcountPlanDetail } from '../types/headcount-plan'

/**
 * Người xem có được thấy TIỀN của kế hoạch này không (tài liệu 06 §7): chỉ người đọc được HĐLĐ của
 * ĐÚNG pháp nhân đó ở phạm vi Tất cả / Công ty. Giao diện không tự tính được phạm vi theo pháp nhân,
 * nên đi theo thứ tự:
 *
 * 1. Không có `labor_contract.read` → không (chặn sớm, khỏi dựng ô tiền rồi mới ẩn).
 * 2. Bản xem trước (`/compute`) đã trả lời → theo nó (`money_hidden`). Nó đi theo pháp nhân ĐANG CHỌN
 *    trên form, còn cờ của chi tiết đi theo pháp nhân đã lưu — nên bản xem trước đứng trước.
 * 3. Chi tiết có `can_see_money` → theo nó.
 * 4. Chưa có gì để suy (form mới, chưa chọn pháp nhân) → cho dựng ô tiền; backend vẫn che lúc lưu.
 */
export function resolveCanSeeMoney(
  canReadContracts: boolean,
  detail: Pick<HeadcountPlanDetail, 'can_see_money'> | null | undefined,
  computed: Pick<HeadcountPlanComputed, 'money_hidden' | 'total'> | null | undefined,
): boolean {
  if (!canReadContracts) return false
  if (computed) return !computed.money_hidden && computed.total !== null
  if (typeof detail?.can_see_money === 'boolean') return detail.can_see_money
  return true
}
