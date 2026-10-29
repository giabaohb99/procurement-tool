import type { ReactNode } from 'react'

import { TableCell, TableRow } from '@/shared/ui/table'
import { cn } from '@/shared/utils/cn'
import { formatMoney } from '@/shared/utils/format-money'
import type { HeadcountPlanActual, HeadcountPlanPeriod } from '../types/headcount-plan'

/** Kỳ con tương lai / bị che: gạch mờ thật, không để trống (trống đọc ra «0»). */
function Dash() {
  return <span className="text-muted-foreground/50">—</span>
}

/** Tổng của các ô có số; cả hàng không có ô nào có số thì `null` (không phải 0). */
function sumKnown(values: readonly (number | null)[]): number | null {
  const known = values.filter((v): v is number => v != null)
  return known.length ? known.reduce((a, b) => a + b, 0) : null
}

function Row({
  label,
  values,
  total,
  render,
  className,
}: {
  label: string
  values: readonly (number | null)[]
  total: number | null
  render: (v: number) => ReactNode
  className?: string
}) {
  return (
    <TableRow className={className}>
      <TableCell>{label}</TableCell>
      {values.map((v, i) => (
        <TableCell key={i} className="text-right tabular-nums">
          {v == null ? <Dash /> : render(v)}
        </TableCell>
      ))}
      <TableCell className="text-right tabular-nums">{total == null ? <Dash /> : render(total)}</TableCell>
    </TableRow>
  )
}

const money = (v: number) => formatMoney(v)
/** Còn dư (dương) / vượt (âm, chữ đỏ) — kế hoạch phần so được trừ thực tế. */
const remaining = (v: number) => <span className={cn(v < 0 && 'font-semibold text-destructive')}>{formatMoney(v)}</span>

interface HeadcountPlanActualRowsProps {
  actual: HeadcountPlanActual
  periods: readonly HeadcountPlanPeriod[]
  showMoney: boolean
}

/**
 * Các dòng THỰC TẾ của bảng tự tính (phase 24) — chỉ ở kế hoạch đã lưu. Số người thực tế luôn hiện;
 * ba dòng tiền chỉ khi được xem lương (bị che thì backend trả `null` cả mảng, dòng bị gỡ hẳn).
 * Cột «Tổng kỳ»: số người lấy kỳ con cuối CÓ số, tiền cộng các kỳ con có số.
 */
export function HeadcountPlanActualRows({ actual, periods, showMoney }: HeadcountPlanActualRowsProps) {
  const pad = (arr: readonly (number | null)[] | null) => periods.map((_, i) => arr?.[i] ?? null)
  const heads = pad(actual.headcount)
  const lastHead = [...heads].reverse().find((v) => v != null) ?? null
  const actualValues = pad(actual.values)
  const planned = pad(actual.planned_comparable)
  const remain = pad(actual.remaining)
  const moneyShown = showMoney && actual.values != null

  return (
    <>
      <Row label="Số người thực tế" values={heads} total={lastHead} render={String} className="border-t-2" />
      {moneyShown && (
        <>
          <Row label="Kế hoạch phần so được" values={planned} total={sumKnown(planned)} render={money} />
          <Row label="Thực tế (phần so được)" values={actualValues} total={sumKnown(actualValues)} render={money} />
          <Row label="Còn dư / vượt" values={remain} total={sumKnown(remain)} render={remaining} className="font-medium" />
        </>
      )}
    </>
  )
}
