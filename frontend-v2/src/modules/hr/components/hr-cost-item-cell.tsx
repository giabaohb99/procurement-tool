import { Input } from '@/shared/ui/input'
import { MultiPicker } from '@/shared/ui/multi-picker'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import {
  COST_ACTUAL_SOURCE,
  COST_APPLIES_TO,
  COST_APPLIES_TO_CODE,
  COST_CALC_METHOD,
  labelOf,
} from '@/shared/constants/statuses'
import type { HrCostGroup, HrCostItem } from '../types/hr-cost'
import { describeCostItemFields } from '../utils/hr-cost-item-rules'
import { CodeSelect, HrCostItemRowActions } from './hr-cost-item-row-controls'
import { HrCostItemParamCell, type HrCostItemParamKey } from './hr-cost-item-param-cell'

/** Mọi thứ một ô cần biết ngoài chính khoản của nó — bảng dựng một lần, truyền cho mọi ô. */
export interface HrCostItemCellContext {
  items: readonly HrCostItem[]
  groups: readonly HrCostGroup[]
  positions: readonly { id: number; name: string }[]
  monthChoices: readonly number[]
  readOnly: boolean
  /** Lỗi sớm theo mã khoản (`listCostItemProblems`). */
  problems: ReadonlyMap<string, string[]>
  onPatch: (index: number, patch: Partial<HrCostItem>) => void
  onMethodChange: (index: number, method: number) => void
  /** `false` = mã mới bị từ chối (rỗng / trùng khoản khác) — ô trả lại mã cũ. */
  onRename: (index: number, code: string) => boolean
  onMove: (index: number, delta: -1 | 1) => void
  onRemove: (index: number) => void
}

const PARAM_KEYS: readonly string[] = ['rate', 'factor', 'cap_amount', 'amount', 'base_codes', 'months']

interface HrCostItemCellProps {
  columnKey: string
  item: HrCostItem
  index: number
  ctx: HrCostItemCellContext
}

/** MỘT ô của bảng khoản chi phí — `LinesTable.renderCell` gọi vào đây theo khóa cột. */
export function HrCostItemCell({ columnKey, item, index, ctx }: HrCostItemCellProps) {
  const { readOnly } = ctx
  if (PARAM_KEYS.includes(columnKey)) {
    return (
      <HrCostItemParamCell
        columnKey={columnKey as HrCostItemParamKey}
        item={item}
        items={ctx.items}
        monthChoices={ctx.monthChoices}
        readOnly={readOnly}
        onPatch={(patch) => ctx.onPatch(index, patch)}
      />
    )
  }
  const label = item.name || item.code
  switch (columnKey) {
    case 'code':
      return readOnly ? (
        <span className="font-mono text-xs">{item.code}</span>
      ) : (
        //  Đổi mã chạy lúc RỜI Ô: mã là khóa tham chiếu (khoản gốc, số tiền của dòng), đổi theo từng
        //  phím thì gõ «LUONG» đi qua «L», «LU»… và mỗi bước đều kéo theo đổi tham chiếu.
        <Input
          key={item.code}
          defaultValue={item.code}
          aria-label={`Mã khoản ${index + 1}`}
          className="font-mono text-xs uppercase"
          maxLength={30}
          onBlur={(e) => {
            if (!ctx.onRename(index, e.target.value)) e.target.value = item.code
          }}
          onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()}
        />
      )
    case 'name': {
      const problems = ctx.problems.get(item.code) ?? []
      return (
        <div className="space-y-1">
          {readOnly ? (
            <span className="font-medium">{item.name}</span>
          ) : (
            <Input
              value={item.name}
              aria-label={`Tên khoản ${index + 1}`}
              maxLength={150}
              onChange={(e) => ctx.onPatch(index, { name: e.target.value })}
              onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()}
            />
          )}
          {!readOnly &&
            problems.map((p) => (
              <p key={p} className="text-xs text-destructive">
                {p}
              </p>
            ))}
        </div>
      )
    }
    case 'group_id': {
      if (readOnly) return <span>{ctx.groups.find((g) => g.id === item.group_id)?.name ?? ''}</span>
      return (
        <Select
          value={item.group_id ? String(item.group_id) : ''}
          onValueChange={(v) => ctx.onPatch(index, { group_id: Number(v) })}
        >
          <SelectTrigger className="w-full" aria-label={`Nhóm của ${label}`}>
            <SelectValue placeholder="Chọn nhóm" />
          </SelectTrigger>
          <SelectContent>
            {ctx.groups.map((g) => (
              <SelectItem key={g.id} value={String(g.id)}>
                {g.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )
    }
    case 'calc_method':
      return readOnly ? (
        <span>{labelOf(COST_CALC_METHOD, String(item.calc_method))}</span>
      ) : (
        <CodeSelect
          value={item.calc_method}
          options={COST_CALC_METHOD}
          label={`Cách tính của ${label}`}
          onChange={(m) => ctx.onMethodChange(index, m)}
        />
      )
    case 'applies_to': {
      const spec = describeCostItemFields(item.calc_method)
      const options = COST_APPLIES_TO.filter(
        (o) => spec.wholeDepartment || Number(o.value) !== COST_APPLIES_TO_CODE.WHOLE_DEPARTMENT,
      )
      const selected = item.applies_to === COST_APPLIES_TO_CODE.SELECTED_POSITIONS
      const positionNames = ctx.positions.filter((p) => item.position_ids.includes(p.id)).map((p) => p.name)
      if (readOnly) {
        return (
          <span>
            {labelOf(COST_APPLIES_TO, String(item.applies_to))}
            {selected && positionNames.length > 0 && `: ${positionNames.join(', ')}`}
          </span>
        )
      }
      return (
        <div className="space-y-1">
          <CodeSelect
            value={item.applies_to}
            options={options}
            label={`Áp cho của ${label}`}
            onChange={(applies_to) => ctx.onPatch(index, { applies_to })}
          />
          {selected && (
            <MultiPicker<number>
              value={item.position_ids}
              onChange={(position_ids) => ctx.onPatch(index, { position_ids })}
              options={ctx.positions.map((p) => ({ id: p.id, label: p.name }))}
              placeholder="Chọn vị trí"
              searchPlaceholder="Tìm chức vụ…"
            />
          )}
        </div>
      )
    }
    case 'actual_source':
      return readOnly ? (
        <span>{labelOf(COST_ACTUAL_SOURCE, String(item.actual_source))}</span>
      ) : (
        <CodeSelect
          value={item.actual_source}
          options={COST_ACTUAL_SOURCE}
          label={`Lấy thực tế từ của ${label}`}
          onChange={(actual_source) => ctx.onPatch(index, { actual_source })}
        />
      )
    case 'actions':
      return (
        <HrCostItemRowActions
          label={label}
          isFirst={index === 0}
          isLast={index === ctx.items.length - 1}
          onMove={(delta) => ctx.onMove(index, delta)}
          onRemove={() => ctx.onRemove(index)}
        />
      )
    default:
      return null
  }
}
