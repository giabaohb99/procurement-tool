/**
 * bao-CR-478 — chép số hàng loạt giữa hai cột giai đoạn của bảng chi phí thu mua
 * («Dự toán → Tạm tính», «Tạm tính → Quyết toán»), cùng luật với nút ở bản cũ.
 *
 * Chỉ điền Ô CÒN TRỐNG (rỗng hoặc 0 — bản cũ lưu ô bỏ trống thành 0) và chỉ ở dòng còn
 * sửa được: số người dùng đã gõ ở cột đích không bao giờ bị đè. Có tick thì chỉ các dòng
 * đã tick. Chép cả tỷ giá đi kèm số tiền, giống backend chép khi quyết toán.
 * Đây chỉ là sửa bảng trên màn hình — muốn ghi lại vẫn phải bấm Lưu.
 */
import type { PurchaseOrderImportCost } from '../types/purchase-order-detail'

export type CostCopySource = 'estimate' | 'provisional'
export type CostCopyTarget = 'provisional' | 'final'

const hasAmount = (value: number | null | undefined) => Number(value) > 0

export function copyCostStageAmounts(
  costs: PurchaseOrderImportCost[],
  from: CostCopySource,
  to: CostCopyTarget,
  canEdit: (cost: PurchaseOrderImportCost) => boolean,
  onlyIds?: ReadonlySet<number>,
): { costs: PurchaseOrderImportCost[]; copied: number } {
  let copied = 0
  const next = costs.map((cost) => {
    if (!canEdit(cost)) return cost
    if (onlyIds && onlyIds.size > 0 && (cost.id === undefined || !onlyIds.has(cost.id))) return cost
    if (hasAmount(cost[`${to}_amount`]) || !hasAmount(cost[`${from}_amount`])) return cost
    copied += 1
    return { ...cost, [`${to}_amount`]: cost[`${from}_amount`], [`${to}_rate`]: cost[`${from}_rate`] }
  })
  return { costs: next, copied }
}
