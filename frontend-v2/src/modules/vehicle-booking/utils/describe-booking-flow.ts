import type { ApprovalInstance } from '@/modules/approval/types/approval'

/**
 * Câu «phiếu này đi theo luồng nào» cho thẻ Tiến trình xử lý (bao-CR-579).
 *
 * Trả `null` khi phiếu chưa vào bộ máy duyệt (đi đường một bước có sẵn) — khi đó
 * không có luồng nào để nói. Phiếu nạp từ app đặt xe cũ mang phiên `flow_id = 0`:
 * đó là bản chép quy trình bên app cũ, không phải luồng khai trên ERP, nên phải
 * nói rõ để người đọc không đi tìm nó trong màn cấu hình luồng.
 */
export function describeBookingFlow(
  instance: Pick<ApprovalInstance, 'flow_id' | 'flow_name' | 'flow_version'> | null | undefined,
): string | null {
  if (!instance) return null
  const name = (instance.flow_name || '').trim()
  if (!instance.flow_id) {
    return name ? `Theo quy trình bên app cũ «${name}»` : 'Theo quy trình bên app cũ'
  }
  const label = name || `Luồng #${instance.flow_id}`
  return instance.flow_version > 1
    ? `Theo luồng «${label}» (bản ${instance.flow_version})`
    : `Theo luồng «${label}»`
}
