import { Separator } from '@/shared/ui/separator'
import { formatMoney } from '@/shared/utils/format-money'

export function PurchaseRequestTotals({
  subtotal,
  vat,
  total,
}: {
  subtotal: number
  vat: number
  total: number
}) {
  return (
    <div className="ml-auto w-full max-w-sm space-y-2 rounded-lg bg-muted/40 p-4 text-sm">
      <MoneyRow label="Tiền hàng (chưa VAT)" value={subtotal} />
      <MoneyRow label="Tiền VAT" value={vat} muted />
      <Separator />
      <MoneyRow label="Tổng cộng (gồm VAT)" value={total} strong />
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
    <div className={muted ? 'flex justify-between gap-4 text-muted-foreground' : 'flex justify-between gap-4'}>
      <span className={strong ? 'font-semibold' : undefined}>{label}</span>
      <span className={`tabular-nums ${strong ? 'font-bold text-navy dark:text-foreground' : 'font-medium'}`}>
        {formatMoney(value)} đ
      </span>
    </div>
  )
}
