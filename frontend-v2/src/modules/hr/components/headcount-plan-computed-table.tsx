import { ChevronDown, ChevronRight, Loader2 } from 'lucide-react'
import { Fragment, useState } from 'react'

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/ui/table'
import { cn } from '@/shared/utils/cn'
import { formatMoney } from '@/shared/utils/format-money'
import type { HeadcountPlanActual, HeadcountPlanComputed, HeadcountPlanPeriod } from '../types/headcount-plan'
import type { HrCostItem } from '../types/hr-cost'
import { buildCostBucketRows, type CostBucketKey } from '../utils/headcount-plan-cost-buckets'
import { HeadcountPlanActualRows } from './headcount-plan-actual-rows'

interface HeadcountPlanComputedTableProps {
  computed: HeadcountPlanComputed | null | undefined
  /** Kỳ con dựng ở giao diện — tiêu đề cột. */
  periods: readonly HeadcountPlanPeriod[]
  /** «Cả năm» (kỳ Năm) · «Tổng kỳ». */
  totalLabel: string
  /** Khoản trên form — để biết khoản nào thuộc dòng Lương / Bảo hiểm / Thưởng. */
  costItems: readonly Pick<HrCostItem, 'code' | 'calc_method'>[]
  /** Số người cần có từng kỳ con (cộng ở giao diện). */
  headcounts: readonly number[]
  showMoney: boolean
  isFetching: boolean
  /** Thực tế so với kế hoạch — chỉ kế hoạch ĐÃ LƯU có (không có ở bản xem trước). */
  actual?: HeadcountPlanActual | null
  /** Ghi chú dưới bảng («Thực tế chưa gồm…», «Q3 đang chạy…»). */
  notes?: readonly string[]
}

/** Ô tiền: `null` (bị che / chưa tính) hiện gạch mờ thật, không để trống. */
function Money({ value, strong }: { value: number | null | undefined; strong?: boolean }) {
  if (value == null) return <span className="text-muted-foreground/50">—</span>
  return <span className={cn('tabular-nums', strong && 'font-semibold')}>{formatMoney(value)}</span>
}

/**
 * Khối ③ TỔNG (tự tính, chỉ đọc — duoc-CR-690): Số người · Lương + phụ cấp · Bảo hiểm · Thưởng, quà, chi
 * khác · TỔNG; dưới đó các dòng Thực tế / Còn dư của kế hoạch đã lưu. Bấm một dòng tiền để mở ra từng chi
 * phí. Không được xem lương thì chỉ còn dòng số người.
 *
 * Con số là của BỘ TÍNH ở backend (`POST /compute`) — giao diện chỉ CỘNG các khoản bộ tính trả về theo
 * cách tính, không tự nhân lương × người (tự tính là sớm muộn lệch với báo cáo đọc cùng bộ tính đó).
 */
export function HeadcountPlanComputedTable({
  computed,
  periods,
  totalLabel,
  costItems,
  headcounts,
  showMoney,
  isFetching,
  actual,
  notes = [],
}: HeadcountPlanComputedTableProps) {
  const [open, setOpen] = useState<Set<CostBucketKey>>(() => new Set())
  const buckets = showMoney && computed && !computed.money_hidden ? buildCostBucketRows(computed.items, costItems, periods.length) : []
  const toggle = (key: CostBucketKey) =>
    setOpen((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })

  return (
    <div className="relative rounded-md border">
      {isFetching && (
        <span className="absolute top-2 right-2 z-10 flex items-center gap-1 text-xs text-muted-foreground">
          <Loader2 className="size-3 animate-spin" />
          Đang tính…
        </span>
      )}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="min-w-44" />
            {periods.map((p) => (
              <TableHead key={p.key} className="min-w-28 text-right">
                {p.label}
              </TableHead>
            ))}
            <TableHead className="min-w-32 text-right">{totalLabel}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>Số người</TableCell>
            {periods.map((p, i) => (
              <TableCell key={p.key} className="text-right tabular-nums">
                {headcounts[i] ?? 0}
              </TableCell>
            ))}
            <TableCell className="text-right tabular-nums">{headcounts.length ? headcounts[headcounts.length - 1] : 0}</TableCell>
          </TableRow>
          {buckets.map((b) => {
            const expanded = open.has(b.key)
            return (
              <Fragment key={b.key}>
                <TableRow>
                  <TableCell>
                    <button type="button" className="flex items-center gap-1" aria-expanded={expanded} onClick={() => toggle(b.key)}>
                      {expanded ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}
                      {b.label}
                    </button>
                  </TableCell>
                  {periods.map((p, i) => (
                    <TableCell key={p.key} className="text-right">
                      <Money value={b.values[i]} />
                    </TableCell>
                  ))}
                  <TableCell className="text-right">
                    <Money value={b.total} />
                  </TableCell>
                </TableRow>
                {expanded &&
                  b.items.map((it) => (
                    <TableRow key={`i${it.code}`} className="text-muted-foreground">
                      <TableCell className="pl-9 whitespace-normal">{it.name}</TableCell>
                      {periods.map((p, i) => (
                        <TableCell key={p.key} className="text-right">
                          <Money value={it.values[i]} />
                        </TableCell>
                      ))}
                      <TableCell className="text-right">
                        <Money value={it.total} />
                      </TableCell>
                    </TableRow>
                  ))}
              </Fragment>
            )
          })}
          {showMoney && (
            <TableRow className="bg-muted/40">
              <TableCell className="font-semibold">TỔNG</TableCell>
              {periods.map((p, i) => (
                <TableCell key={p.key} className="text-right">
                  <Money value={computed?.total?.values[i]} strong />
                </TableCell>
              ))}
              <TableCell className="text-right">
                <Money value={computed?.total?.total} strong />
              </TableCell>
            </TableRow>
          )}
          {actual && <HeadcountPlanActualRows actual={actual} periods={periods} showMoney={showMoney} />}
        </TableBody>
      </Table>
      {notes.length > 0 && (
        <ul className="space-y-0.5 border-t px-3 py-2 text-xs text-muted-foreground">
          {notes.map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
