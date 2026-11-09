import { ACTION_TONE_CLASS } from '@/shared/ui/action-tone'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import type { ImportCostSummaryBySupplier } from '../types/purchase-order-detail'

interface PurchaseOrderImportCostSupplierPayActionProps {
  group: Pick<ImportCostSummaryBySupplier, 'remaining' | 'unpaid_payable_ids'>
  onCreatePaymentRequest: (payableIds: number[]) => void
  className?: string
}

/**
 * Ô cuối của một NCC trong bảng *Thanh toán chi phí theo nhà cung cấp* — dùng chung cho bảng
 * khổ rộng và thẻ khổ điện thoại. Ba nhánh theo đúng bản v1 (duoc-CR-741):
 *
 * - còn khoản nợ chưa trả → nút **Tạo YCTT**;
 * - còn phải chi nhưng chưa có khoản nợ nào (chưa chọn NCC, dòng chưa Lưu, số tiền 0) → chữ
 *   **Chưa thành công nợ** (bao-CR-379: trước đây nhánh này rơi nhầm vào nút bấm không được);
 * - hết nợ → huy hiệu **Đã chi đủ**.
 */
export function PurchaseOrderImportCostSupplierPayAction({
  group,
  onCreatePaymentRequest,
  className,
}: PurchaseOrderImportCostSupplierPayActionProps) {
  if (group.unpaid_payable_ids.length > 0) {
    return (
      <Button
        type="button"
        size="sm"
        variant="outline"
        className={cn(ACTION_TONE_CLASS.accent, className)}
        onClick={() => onCreatePaymentRequest(group.unpaid_payable_ids)}
      >
        Tạo YCTT
      </Button>
    )
  }
  if (group.remaining > 0.01) {
    return (
      <span
        className={cn('text-xs text-muted-foreground', className)}
        title="Các khoản này chưa thành công nợ (chưa chọn NCC, dòng chưa Lưu hoặc số tiền 0) nên chưa lập phiếu được"
      >
        Chưa thành công nợ
      </span>
    )
  }
  return (
    <Badge variant="outline" className={className}>
      Đã chi đủ
    </Badge>
  )
}
