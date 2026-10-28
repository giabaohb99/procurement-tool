import { MultiPicker } from '@/shared/ui/multi-picker'
import { NumberInput, PRICE_MAX_DECIMALS } from '@/shared/ui/number-input'
import { formatMoney, formatPercent } from '@/shared/utils/format-money'
import type { HrCostItem } from '../types/hr-cost'
import { describeCostItemFields, listBaseCandidates } from '../utils/hr-cost-item-rules'

/** Ô không có nghĩa với cách tính này — gạch mờ, KHÔNG để trống (trống đọc ra «chưa nhập»). */
function NotApplicable() {
  return (
    <span className="text-muted-foreground/50" title="Không dùng với cách tính này">
      —
    </span>
  )
}

export type HrCostItemParamKey = 'rate' | 'factor' | 'cap_amount' | 'amount' | 'base_codes' | 'months'

interface HrCostItemParamCellProps {
  columnKey: HrCostItemParamKey
  item: HrCostItem
  items: readonly HrCostItem[]
  /** Tháng chọn được: 12 tháng ở màn Mẫu, đúng các tháng của kỳ ở màn Kế hoạch. */
  monthChoices: readonly number[]
  readOnly: boolean
  onPatch: (patch: Partial<HrCostItem>) => void
}

/**
 * Các ô THÔNG SỐ của một khoản — có hay không tùy cách tính (`describeCostItemFields`): tỷ lệ %,
 * hệ số, trần / người, số tiền, khoản gốc, tháng rơi vào. Hai ô tiền chỉ được dựng khi bảng cho xem
 * tiền — bảng tự gỡ cột đó đi, nên ô này không phải tự kiểm quyền.
 */
export function HrCostItemParamCell({
  columnKey,
  item,
  items,
  monthChoices,
  readOnly,
  onPatch,
}: HrCostItemParamCellProps) {
  const spec = describeCostItemFields(item.calc_method)
  const label = item.name || item.code

  switch (columnKey) {
    case 'rate':
      if (!spec.rate) return <NotApplicable />
      return readOnly ? (
        <span className="tabular-nums">{formatPercent(item.rate)}</span>
      ) : (
        <NumberInput
          aria-label={`Tỷ lệ % của ${label}`}
          value={item.rate ?? 0}
          maxDecimals={PRICE_MAX_DECIMALS}
          max={100}
          onChange={(rate) => onPatch({ rate })}
        />
      )
    case 'factor':
      if (!spec.factor) return <NotApplicable />
      return readOnly ? (
        <span className="tabular-nums">{item.factor ?? ''}</span>
      ) : (
        <NumberInput
          aria-label={`Hệ số của ${label}`}
          value={item.factor ?? 0}
          maxDecimals={2}
          onChange={(factor) => onPatch({ factor })}
        />
      )
    case 'cap_amount':
    case 'amount': {
      const applies = columnKey === 'cap_amount' ? spec.cap : spec.amount
      if (!applies) return <NotApplicable />
      const value = item[columnKey]
      return readOnly ? (
        <span className="tabular-nums">{value ? formatMoney(value) : ''}</span>
      ) : (
        <NumberInput
          aria-label={`${columnKey === 'cap_amount' ? 'Trần / người' : 'Số tiền'} của ${label}`}
          value={value ?? 0}
          decimals={false}
          placeholder={columnKey === 'cap_amount' ? 'Không trần' : undefined}
          onChange={(next) => onPatch({ [columnKey]: next })}
        />
      )
    }
    case 'base_codes': {
      if (!spec.baseCodes) return <NotApplicable />
      const candidates = listBaseCandidates(items, item)
      const names = new Map(items.map((i) => [i.code, i.name || i.code]))
      if (readOnly) return <span>{item.base_codes.map((c) => names.get(c) ?? c).join(' + ')}</span>
      return (
        <MultiPicker<string>
          value={item.base_codes}
          onChange={(codes) => onPatch({ base_codes: spec.baseCodes === 'one' ? codes.slice(-1) : codes })}
          options={candidates.map((c) => ({ id: c.code, label: c.name || c.code, hint: c.code }))}
          placeholder={spec.baseCodes === 'one' ? 'Chọn một khoản gốc' : 'Chọn khoản gốc'}
          emptyMessage="Chưa có khoản «nhập theo vị trí» nào để làm gốc."
        />
      )
    }
    case 'months': {
      const sorted = [...item.months].sort((a, b) => a - b)
      if (readOnly) return <span>{sorted.length ? sorted.map((m) => `T${m}`).join(', ') : 'Mỗi tháng'}</span>
      //  Tháng đã lưu mà nằm ngoài kỳ (mẫu khai T12, kế hoạch là Q3) vẫn phải hiện để người dùng thấy
      //  và gỡ — lọc mất khỏi ô là nó vẫn nằm trong dữ liệu và backend chặn mà không ai hiểu vì sao.
      const choices = [...new Set([...monthChoices, ...item.months])].sort((a, b) => a - b)
      return (
        <MultiPicker<number>
          value={sorted}
          onChange={(months) => onPatch({ months })}
          options={choices.map((m) => ({
            id: m,
            label: `T${m}`,
            hint: monthChoices.includes(m) ? undefined : 'ngoài kỳ',
          }))}
          placeholder={spec.monthsRequired ? 'Chọn tháng' : 'Mỗi tháng'}
        />
      )
    }
  }
}
