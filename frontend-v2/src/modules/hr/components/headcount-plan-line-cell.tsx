import { Trash2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { NumberInput } from '@/shared/ui/number-input'
import { cn } from '@/shared/utils/cn'
import { formatMoney } from '@/shared/utils/format-money'
import { AMOUNT_COLUMN_PREFIX, HEADCOUNT_COLUMN_PREFIX } from '../config/headcount-plan-line-columns'
import { COST_ACTUAL_SOURCE_CODE } from '@/shared/constants/statuses'
import {
  NO_POSITION_ID,
  NO_POSITION_LABEL,
  type HeadcountPlanLine,
  type HeadcountPlanPositionStat,
} from '../types/headcount-plan'
import type { HrCostItem } from '../types/hr-cost'
import { computeNeedToHire } from '../utils/headcount-plan-draft'
import { isItemAppliedToPosition } from '../utils/hr-cost-item-rules'

export interface HeadcountPlanLineCellContext {
  items: readonly HrCostItem[]
  stats: readonly HeadcountPlanPositionStat[]
  /** «Đang có» đã tính sẵn cho từng dòng (theo chỉ số). */
  currentCounts: readonly number[]
  showMoney: boolean
  readOnly: boolean
  onPatch: (index: number, patch: Partial<HeadcountPlanLine>) => void
  onRemove: (index: number) => void
}

/** Gợi ý BÌNH QUÂN HIỆN TẠI bên ô lương — chỉ khoản khai «Lấy thực tế từ» lương / phụ cấp trên HĐ. */
function findAverageHint(item: HrCostItem, stat: HeadcountPlanPositionStat | undefined): number | null {
  if (!stat) return null
  if (item.actual_source === COST_ACTUAL_SOURCE_CODE.BASE_SALARY) return stat.avg_base_salary
  if (item.actual_source === COST_ACTUAL_SOURCE_CODE.ALLOWANCE) return stat.avg_allowance
  return null
}

interface HeadcountPlanLineCellProps {
  columnKey: string
  line: HeadcountPlanLine
  index: number
  ctx: HeadcountPlanLineCellContext
}

/** MỘT ô của bảng định biên theo vị trí — `LinesTable.renderCell` gọi vào đây theo khóa cột. */
export function HeadcountPlanLineCell({ columnKey, line, index, ctx }: HeadcountPlanLineCellProps) {
  const positionLabel =
    line.position_id === NO_POSITION_ID ? NO_POSITION_LABEL : line.position_name || `#${line.position_id}`

  if (columnKey.startsWith(HEADCOUNT_COLUMN_PREFIX)) {
    const k = Number(columnKey.slice(HEADCOUNT_COLUMN_PREFIX.length))
    const value = line.headcounts[k] ?? 0
    if (ctx.readOnly) return <span className="tabular-nums">{value}</span>
    return (
      <NumberInput
        aria-label={`Định biên kỳ ${k + 1} của ${positionLabel}`}
        value={value}
        decimals={false}
        placeholder="0"
        onChange={(n) => ctx.onPatch(index, { headcounts: line.headcounts.map((h, j) => (j === k ? n : h)) })}
      />
    )
  }

  if (columnKey.startsWith(AMOUNT_COLUMN_PREFIX)) {
    const code = columnKey.slice(AMOUNT_COLUMN_PREFIX.length)
    const item = ctx.items.find((i) => i.code === code)
    if (!item) return null
    if (!isItemAppliedToPosition(item, line.position_id)) {
      return (
        <span className="text-muted-foreground/50" title="Khoản này không áp cho vị trí này">
          —
        </span>
      )
    }
    const value = line.amounts?.[code] ?? null
    const hint = findAverageHint(item, ctx.stats.find((s) => s.position_id === line.position_id))
    return (
      <div className="space-y-0.5">
        {ctx.readOnly ? (
          <span className="tabular-nums">{value ? formatMoney(value) : ''}</span>
        ) : (
          <NumberInput
            aria-label={`${item.name || item.code} của ${positionLabel}`}
            value={value ?? 0}
            decimals={false}
            onChange={(n) => ctx.onPatch(index, { amounts: { ...line.amounts, [code]: n } })}
          />
        )}
        {hint != null && hint > 0 && (
          <p className="text-right text-[11px] text-muted-foreground" title="Bình quân trên HĐLĐ đang hiệu lực">
            BQ hiện tại {formatMoney(hint)}
          </p>
        )}
      </div>
    )
  }

  switch (columnKey) {
    case 'position':
      return (
        <span className={cn('font-medium', line.position_id === NO_POSITION_ID && 'italic')}>{positionLabel}</span>
      )
    case 'current':
      return <span className="tabular-nums">{ctx.currentCounts[index] ?? 0}</span>
    case 'need': {
      const need = computeNeedToHire(line, ctx.currentCounts[index] ?? 0)
      if (need < 0) {
        return (
          <span className="tabular-nums text-amber-600" title={`Đang dư ${-need} người so với định biên cuối kỳ`}>
            {need}
          </span>
        )
      }
      return <span className={cn('tabular-nums', need > 0 && 'font-semibold text-primary')}>{need}</span>
    }
    case 'note':
      return ctx.readOnly ? (
        <span>{line.note}</span>
      ) : (
        <Input
          value={line.note}
          maxLength={500}
          aria-label={`Ghi chú của ${positionLabel}`}
          onChange={(e) => ctx.onPatch(index, { note: e.target.value })}
          onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()}
        />
      )
    case 'actions':
      return (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="size-7 text-destructive"
          title="Bỏ dòng"
          aria-label={`Bỏ dòng ${positionLabel}`}
          onClick={() => ctx.onRemove(index)}
        >
          <Trash2 className="size-4" />
        </Button>
      )
    default:
      return null
  }
}
