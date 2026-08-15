import { Separator } from '@/shared/ui/separator'
import { formatMoney } from '@/shared/utils/format-money'

interface DocumentMoneyTotalsProps {
  subtotal: number
  vat: number
  total: number
  /** ĐMH gọi tên khác YCMH ("theo SL đặt") nên nhãn để chỗ gọi tự đặt. */
  subtotalLabel?: string
  totalLabel?: string
}

/** Khối tổng tiền cuối bảng dòng hàng — dùng chung cho YCMH và ĐMH. */
export function DocumentMoneyTotals({
  subtotal,
  vat,
  total,
  subtotalLabel = 'Tiền hàng (chưa VAT)',
  totalLabel = 'Tổng cộng (gồm VAT)',
}: DocumentMoneyTotalsProps) {
  return (
    <div className="ml-auto w-full max-w-sm space-y-2 py-2 text-sm">
      <MoneyRow label={subtotalLabel} value={subtotal} />
      <MoneyRow label="Tiền VAT" value={vat} muted />
      <Separator />
      <MoneyRow label={totalLabel} value={total} strong />
    </div>
  )
}

function MoneyRow({
  label,
  value,
  muted,
  strong,
}: {
  label: string
  value: number
  muted?: boolean
  strong?: boolean
}) {
  return (
    <div
      className={
        muted ? 'flex justify-between gap-4 text-muted-foreground' : 'flex justify-between gap-4'
      }
    >
      <span className={strong ? 'font-semibold' : undefined}>{label}</span>
      <span
        className={`tabular-nums ${strong ? 'font-bold text-navy dark:text-foreground' : 'font-medium'}`}
      >
        {formatMoney(value)} đ
      </span>
    </div>
  )
}
