import { useState, type ReactNode } from 'react'

import { COST_CALC_METHOD_CODE } from '@/shared/constants/statuses'
import { NumberInput } from '@/shared/ui/number-input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { formatMoney, formatPercent, formatQuantity } from '@/shared/utils/format-money'
import type { HrCostItem } from '../types/hr-cost'
import { HIDDEN_MONEY_TEXT } from '../utils/hr-cost-item-describe'
import { pickDefaultPercentBases } from '../utils/hr-cost-item-kind'

const M = COST_CALC_METHOD_CODE
/** Giá trị «chia đều» của ô tháng — khoản cả phòng không chọn tháng thì backend chia đều mọi tháng của kỳ. */
const SPREAD = '0'

interface HeadcountPlanOtherCostSentenceProps {
  item: HrCostItem
  /** Mọi khoản khác của kế hoạch — để đọc «trên lương + phụ cấp». */
  others: readonly HrCostItem[]
  periodMonths: readonly number[]
  editable: boolean
  showMoney: boolean
  onChange: (patch: Partial<HrCostItem>) => void
}

/** Ô số chèn giữa câu; không sửa được thì chữ đậm. `money` + không được xem tiền → «(ẩn số tiền)». */
function Slot({
  value,
  label,
  editable,
  money,
  showMoney,
  decimals,
  width,
  onChange,
}: {
  value: number | null
  label: string
  editable: boolean
  money?: boolean
  showMoney: boolean
  decimals?: boolean
  width: string
  onChange: (n: number) => void
}) {
  if (money && !showMoney) return <span className="text-muted-foreground">{HIDDEN_MONEY_TEXT}</span>
  if (!editable) {
    const text = money ? formatMoney(value ?? 0) : decimals ? formatQuantity(value ?? 0) : String(value ?? 0)
    return <strong className="tabular-nums">{text}</strong>
  }
  return (
    <NumberInput
      aria-label={label}
      value={value ?? 0}
      decimals={Boolean(decimals)}
      maxDecimals={2}
      placeholder="0"
      className={cn('h-8 text-right', width)}
      onChange={onChange}
    />
  )
}

/** Ô «chi tháng»: tháng của kỳ (giữ cả tháng đang lưu dù đã ra ngoài kỳ, để lỗi nói được là tháng nào). */
function MonthSlot({ item, periodMonths, editable, spread, onChange }: {
  item: HrCostItem
  periodMonths: readonly number[]
  editable: boolean
  spread: boolean
  onChange: (months: number[]) => void
}) {
  const current = item.months[0]
  if (!editable) return <strong>{current ? `T${current}` : 'chia đều các tháng'}</strong>
  const months = [...new Set([...periodMonths, ...item.months])].sort((a, b) => a - b)
  return (
    <Select value={current ? String(current) : spread ? SPREAD : ''} onValueChange={(v) => onChange(v === SPREAD ? [] : [Number(v)])}>
      <SelectTrigger size="sm" className="h-8 w-auto min-w-20" aria-label={`Tháng chi của ${item.name}`}>
        <SelectValue placeholder="Chọn" />
      </SelectTrigger>
      <SelectContent>
        {spread && <SelectItem value={SPREAD}>Chia đều các tháng</SelectItem>}
        {months.map((m) => (
          <SelectItem key={m} value={String(m)}>{`T${m}`}</SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

/** Mức tối đa của khoản % — chỉ hiện khi khoản có trần; bấm vào mới mở ô sửa. */
function CapLink({ item, editable, onChange }: { item: HrCostItem; editable: boolean; onChange: (n: number) => void }) {
  const [editing, setEditing] = useState(false)
  const cap = Number(item.cap_amount) || 0
  if (editing) {
    return (
      <span className="inline-flex items-center gap-1 text-muted-foreground">
        tối đa
        <NumberInput aria-label={`Mức tối đa của ${item.name}`} value={cap} decimals={false} className="h-8 w-32 text-right" onChange={onChange} />
        đ/người
      </span>
    )
  }
  if (cap <= 0) return null
  const text = `tối đa ${formatMoney(cap)} đ/người`
  if (!editable) return <span className="text-xs text-muted-foreground">({text})</span>
  return (
    <button type="button" className="text-xs text-muted-foreground underline decoration-dotted" title="Bấm để sửa mức tối đa" onClick={() => setEditing(true)}>
      ({text})
    </button>
  )
}

/**
 * CÂU sửa tại chỗ của một dòng «Chi phí khác» (duoc-CR-690) — ô số chèn giữa câu, không hộp thoại:
 * «[23,5] % trên lương + phụ cấp» · «[1] tháng lương, chi tháng [12]» · «[500.000] đ/người, chi tháng [3]»
 * · «[50.000.000] đ cả phòng, chi tháng [6]».
 */
export function HeadcountPlanOtherCostSentence({ item, others, periodMonths, editable, showMoney, onChange }: HeadcountPlanOtherCostSentenceProps) {
  //  Khoản % tự tính trên MỌI khoản «tiền / người / tháng» đang dùng — đọc tên chúng ra: «lương + phụ cấp».
  const bases = pickDefaultPercentBases(others.filter((o) => !o.excluded))
    .map((code) => others.find((o) => o.code === code)?.name.trim().toLowerCase())
    .filter(Boolean)
    .join(' + ')
  const slot = (key: 'rate' | 'factor' | 'amount', label: string, width: string, opts: { money?: boolean; decimals?: boolean } = {}) => (
    <Slot
      value={item[key]}
      label={`${label} của ${item.name}`}
      editable={editable}
      showMoney={showMoney}
      width={width}
      onChange={(n) => onChange(key === 'rate' ? { rate: n } : key === 'factor' ? { factor: n } : { amount: n })}
      {...opts}
    />
  )
  const month = (spread: boolean) => (
    <MonthSlot item={item} periodMonths={periodMonths} editable={editable} spread={spread} onChange={(months) => onChange({ months })} />
  )
  let parts: ReactNode
  switch (item.calc_method) {
    case M.PERCENT_OF:
      parts = (
        <>
          {editable ? slot('rate', 'Tỷ lệ %', 'w-20', { decimals: true }) : <strong>{formatPercent(item.rate ?? 0)}</strong>}
          <span>{editable ? '% ' : ''}trên {bases || 'lương'}</span>
          {showMoney && <CapLink item={item} editable={editable} onChange={(n) => onChange({ cap_amount: n })} />}
        </>
      )
      break
    case M.MONTHS_OF:
      parts = (<>{slot('factor', 'Số tháng lương', 'w-16', { decimals: true })}<span>tháng lương, chi tháng</span>{month(false)}</>)
      break
    case M.PER_HEAD_ONCE:
      parts = (<>{slot('amount', 'Số tiền mỗi người', 'w-32', { money: true })}<span>đ/người, chi tháng</span>{month(false)}</>)
      break
    case M.LUMP_SUM:
      parts = (<>{slot('amount', 'Số tiền cả phòng', 'w-36', { money: true })}<span>đ cả phòng, chi tháng</span>{month(true)}</>)
      break
    default:
      parts = <span className="text-muted-foreground">Cách tính chưa hỗ trợ</span>
  }
  return <div className="flex flex-wrap items-center gap-x-1.5 gap-y-1 text-sm">{parts}</div>
}
