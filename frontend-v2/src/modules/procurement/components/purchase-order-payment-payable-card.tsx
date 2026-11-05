import { Checkbox } from '@/shared/ui/checkbox'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import type { Payable } from '../api/purchase-order-payment-api'

interface PurchaseOrderPaymentPayableCardProps {
  payable: Payable
  /** Nhãn bên nhận theo tab đang mở (NCC / Đơn vị vận chuyển / NCC nhận tiền) — như tiêu đề cột của bảng. */
  supplierLabel: string
  checked: boolean
  onCheckedChange: (checked: boolean) => void
}

/**
 * Một KHOẢN CÔNG NỢ trong hộp *Tạo yêu cầu thanh toán* của ĐMH, ở khổ điện thoại.
 *
 * Bảng 7 cột trong hộp thoại 96vw chỉ còn thấy ô tick + tên NCC, mà thứ người
 * dùng cần để quyết định tick là số hóa đơn và số CÒN LẠI. Cả thẻ là một
 * `<label>` bọc ô tick nên chạm bất kỳ đâu trên thẻ cũng tick được — vùng chạm
 * 16px của ô tick là quá nhỏ cho ngón tay.
 */
export function PurchaseOrderPaymentPayableCard({
  payable,
  supplierLabel,
  checked,
  onCheckedChange,
}: PurchaseOrderPaymentPayableCardProps) {
  return (
    <label className="flex cursor-pointer items-start gap-3 px-3 py-2.5">
      <Checkbox
        className="mt-0.5"
        checked={checked}
        onCheckedChange={(next) => onCheckedChange(next === true)}
        aria-label={`Chọn hóa đơn ${payable.invoice_no || payable.id}`}
      />
      <span className="block min-w-0 flex-1 space-y-1">
        <span className="block text-xs text-muted-foreground">{supplierLabel}</span>
        <span className="line-clamp-2 block text-sm font-medium">
          {payable.supplier_name || payable.supplier_code || '—'}
        </span>
        <span className="flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
          <span>
            HĐ{' '}
            <span className="font-medium text-sky-600 dark:text-sky-400">
              {payable.invoice_no || '—'}
            </span>
          </span>
          {payable.incur_date && (
            <span>
              <span aria-hidden="true">· </span>
              {formatDate(payable.incur_date)}
            </span>
          )}
        </span>
        <span className="grid grid-cols-[repeat(auto-fit,minmax(6.5rem,1fr))] gap-2 text-xs">
          <span>
            <span className="block text-muted-foreground">Phải trả</span>
            <span className="tabular-nums">{formatMoney(payable.total)} đ</span>
          </span>
          <span>
            <span className="block text-muted-foreground">Đã trả</span>
            <span className="tabular-nums text-success">{formatMoney(payable.paid_amount)} đ</span>
          </span>
          <span>
            <span className="block text-muted-foreground">Còn lại</span>
            <span className="font-semibold tabular-nums text-destructive">
              {formatMoney(payable.remaining)} đ
            </span>
          </span>
        </span>
      </span>
    </label>
  )
}
