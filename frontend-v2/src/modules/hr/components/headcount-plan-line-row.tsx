import { Trash2 } from 'lucide-react'

import { COST_ACTUAL_SOURCE_CODE } from '@/shared/constants/statuses'
import { Button } from '@/shared/ui/button'
import { NumberInput } from '@/shared/ui/number-input'
import { TableCell, TableRow } from '@/shared/ui/table'
import { cn } from '@/shared/utils/cn'
import { formatMoney } from '@/shared/utils/format-money'
import {
  NO_POSITION_ID,
  NO_POSITION_LABEL,
  type HeadcountPlanLine,
  type HeadcountPlanPeriod,
  type HeadcountPlanPositionStat,
} from '../types/headcount-plan'
import type { HrCostItem } from '../types/hr-cost'
import { computeNeedToHire, fillLineHeadcounts } from '../utils/headcount-plan-draft'
import { ALLOWANCE_CODE, SALARY_CODE, describePerHeadColumn } from '../utils/hr-cost-item-presets'
import { isItemAppliedToPosition } from '../utils/hr-cost-item-rules'
import { HeadcountPlanFillPeriodsButton } from './headcount-plan-fill-periods-button'

/** Gợi ý BÌNH QUÂN HIỆN TẠI dưới ô lương / phụ cấp — theo nguồn thực tế của khoản, vắng thì theo mã. */
function findAverageHint(item: HrCostItem, stat: HeadcountPlanPositionStat | undefined): number | null {
  if (!stat) return null
  const S = COST_ACTUAL_SOURCE_CODE
  if (item.actual_source === S.BASE_SALARY || (!item.actual_source && item.code === SALARY_CODE)) return stat.avg_base_salary
  if (item.actual_source === S.ALLOWANCE || (!item.actual_source && item.code === ALLOWANCE_CODE)) return stat.avg_allowance
  return null
}

interface AmountCellProps {
  item: HrCostItem
  line: HeadcountPlanLine
  positionLabel: string
  stat: HeadcountPlanPositionStat | undefined
  readOnly: boolean
  onChange: (value: number) => void
}

/**
 * Ô tiền / người / tháng. Trống hoặc 0 = dùng MỨC CHUNG của khoản (backend tính vậy) — chỉ gợi ý bằng
 * placeholder, KHÔNG chép mức chung vào ô: chép vào thì đổi mức chung sau đó không còn ăn vào vị trí này.
 */
function AmountCell({ item, line, positionLabel, stat, readOnly, onChange }: AmountCellProps) {
  if (!isItemAppliedToPosition(item, line.position_id)) {
    return <span className="text-muted-foreground/50" title="Không áp cho vị trí này">—</span>
  }
  const value = line.amounts?.[item.code] ?? null
  const common = Number(item.amount) > 0 ? formatMoney(Number(item.amount)) : undefined
  const hint = findAverageHint(item, stat)
  return (
    <div className="space-y-0.5">
      {readOnly ? (
        <span className={cn('block text-right leading-8 tabular-nums', !value && 'text-muted-foreground')}>{value ? formatMoney(value) : (common ?? '')}</span>
      ) : (
        <NumberInput
          aria-label={`${describePerHeadColumn(item)} của ${positionLabel}`}
          value={value ?? 0}
          decimals={false}
          placeholder={common}
          className="h-8 min-w-28 text-right"
          onChange={onChange}
        />
      )}
      {hint != null && hint > 0 && (
        <p className="text-right text-[11px] text-muted-foreground" title="Bình quân trên hợp đồng lao động đang hiệu lực">
          BQ hiện tại {formatMoney(hint)}
        </p>
      )}
    </div>
  )
}

interface HeadcountPlanLineRowProps {
  line: HeadcountPlanLine
  periods: readonly HeadcountPlanPeriod[]
  /** Khoản «tiền / người / tháng» — mỗi khoản một cột (rỗng khi không được xem tiền). */
  moneyItems: readonly HrCostItem[]
  current: number
  stat: HeadcountPlanPositionStat | undefined
  fillLabel: string
  readOnly: boolean
  onPatch: (patch: Partial<HeadcountPlanLine>) => void
  onRemove: () => void
}

/** MỘT dòng của bảng «Người và lương»: vị trí · hiện có · cần có từng kỳ · cần tuyển · tiền / người · xóa. */
export function HeadcountPlanLineRow({
  line,
  periods,
  moneyItems,
  current,
  stat,
  fillLabel,
  readOnly,
  onPatch,
  onRemove,
}: HeadcountPlanLineRowProps) {
  const whole = line.position_id === NO_POSITION_ID
  const positionLabel = whole ? NO_POSITION_LABEL : line.position_name || `#${line.position_id}`
  const need = computeNeedToHire(line, current)

  return (
    <TableRow>
      <TableCell className="align-top whitespace-normal">
        <p className={cn('font-medium', whole && 'italic')}>{positionLabel}</p>
        {!readOnly && periods.length > 1 && (
          <HeadcountPlanFillPeriodsButton
            label={fillLabel}
            positionLabel={positionLabel}
            onFill={(n) => onPatch({ headcounts: fillLineHeadcounts(line, n).headcounts })}
          />
        )}
      </TableCell>
      <TableCell className="text-right align-top leading-8 tabular-nums">{current}</TableCell>
      {periods.map((p, k) => (
        <TableCell key={p.key} className="align-top">
          {readOnly ? (
            <span className="block text-right leading-8 tabular-nums">{line.headcounts[k] ?? 0}</span>
          ) : (
            <NumberInput
              aria-label={`Cần có ${p.label} của ${positionLabel}`}
              value={line.headcounts[k] ?? 0}
              decimals={false}
              placeholder="0"
              className="h-8 min-w-12 text-right"
              onChange={(n) => onPatch({ headcounts: line.headcounts.map((h, j) => (j === k ? n : h)) })}
            />
          )}
        </TableCell>
      ))}
      <TableCell className="text-right align-top leading-8 tabular-nums">
        <span
          className={cn(need > 0 && 'font-semibold text-primary', need < 0 && 'text-amber-600')}
          title={need < 0 ? `Đang dư ${-need} người so với số cần có cuối kỳ` : undefined}
        >
          {need}
        </span>
      </TableCell>
      {moneyItems.map((item) => (
        <TableCell key={item.code} className="align-top">
          <AmountCell
            item={item}
            line={line}
            positionLabel={positionLabel}
            stat={stat}
            readOnly={readOnly}
            onChange={(n) => onPatch({ amounts: { ...line.amounts, [item.code]: n } })}
          />
        </TableCell>
      ))}
      {!readOnly && (
        <TableCell className="align-top">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="size-8 text-destructive"
            title="Xóa dòng"
            aria-label={`Xóa dòng ${positionLabel}`}
            onClick={onRemove}
          >
            <Trash2 className="size-4" />
          </Button>
        </TableCell>
      )}
    </TableRow>
  )
}
