import { Separator } from '@/shared/ui/separator'
import { cn } from '@/shared/utils/cn'
import { formatMoneyWithCurrency } from '@/shared/utils/format-money'

interface DocumentMoneyTotalsProps {
  subtotal: number
  vat: number
  total: number
  /** ĐMH gọi tên khác YCMH ("theo SL đặt") nên nhãn để chỗ gọi tự đặt. */
  subtotalLabel?: string
  totalLabel?: string
  /**
   * bao-CR-319: đơn nhập khẩu tính bằng nguyên tệ — mã tiền tệ thay cho "đ" và giữ
   * số lẻ (5.230,50 USD chứ không phải "5.230 đ"). Bỏ trống / "VND" là tiền Việt.
   */
  currency?: string
}

/** Khối tổng tiền cuối bảng dòng hàng — dùng chung cho YCMH và ĐMH. */
export function DocumentMoneyTotals({
  subtotal,
  vat,
  total,
  subtotalLabel = 'Tiền hàng (chưa VAT)',
  totalLabel = 'Tổng cộng (gồm VAT)',
  currency,
}: DocumentMoneyTotalsProps) {
  return (
    <div className="ml-auto w-full max-w-sm space-y-2 py-2 text-sm">
      <MoneyRow label={subtotalLabel} value={subtotal} currency={currency} />
      <MoneyRow label="Tiền VAT" value={vat} currency={currency} muted />
      <Separator />
      <MoneyRow label={totalLabel} value={total} currency={currency} strong />
    </div>
  )
}

function MoneyRow({
  label,
  value,
  currency,
  muted,
  strong,
}: {
  label: string
  value: number
  currency?: string
  muted?: boolean
  strong?: boolean
}) {
  return (
    <div className={cn('flex justify-between gap-4', muted && 'text-muted-foreground')}>
      <span className={cn(strong && 'font-semibold')}>{label}</span>
      <span
        className={cn('tabular-nums', strong ? 'font-bold text-navy dark:text-foreground' : 'font-medium')}
      >
        {formatMoneyWithCurrency(value, currency)}
      </span>
    </div>
  )
}
