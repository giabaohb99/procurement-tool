import { AlertCircle, Plus } from 'lucide-react'
import { useMemo } from 'react'

import { LinesTable } from '@/shared/data-table/lines-table'
import { Button } from '@/shared/ui/button'
import { buildCostItemColumns } from '../config/hr-cost-item-columns'
import type { HeadcountPlanLine } from '../types/headcount-plan'
import type { HrCostGroup, HrCostItem } from '../types/hr-cost'
import {
  changeCostItemMethod,
  createEmptyCostItem,
  listCostItemProblems,
  moveCostItem,
  normalizeCostCode,
  removeCostItem,
  renameCostItemCode,
} from '../utils/hr-cost-item-rules'
import { HrCostItemCell, type HrCostItemCellContext } from './hr-cost-item-cell'

const ALL_MONTHS = Array.from({ length: 12 }, (_, i) => i + 1)

interface HrCostItemsEditorProps {
  items: HrCostItem[]
  /** Dòng vị trí của kế hoạch — đổi / bỏ mã khoản thì đổi theo số tiền của dòng. Màn Mẫu không có. */
  lines?: HeadcountPlanLine[]
  onChange: (next: { items: HrCostItem[]; lines: HeadcountPlanLine[] }) => void
  groups: readonly HrCostGroup[]
  positions: readonly { id: number; name: string }[]
  /** Tháng của kỳ kế hoạch; vắng = màn Mẫu, chọn được cả 12 tháng và không kiểm «ngoài kỳ». */
  periodMonths?: readonly number[]
  showMoney: boolean
  readOnly: boolean
  /** Khóa nhớ bố cục cột — hai màn hai khóa, bảng của màn này không đè bố cục màn kia. */
  storageKey: string
  /** Câu lỗi kiểm hợp lệ của máy chủ (422 từ `/compute`) — bày ngay trên bảng. */
  serverError?: string
}

/**
 * BẢNG KHOẢN CHI PHÍ dùng chung cho màn Mẫu khoản chi phí và khối 2 của trang Kế hoạch (tài liệu 06
 * §2.2 + §4). Sửa tại chỗ trên `LinesTable`; mọi đổi trạng thái đi qua hàm thuần ở
 * `hr-cost-item-rules.ts` để giữ tham chiếu mã ↔ khoản gốc ↔ số tiền của dòng luôn khớp.
 */
export function HrCostItemsEditor({
  items,
  lines = [],
  onChange,
  groups,
  positions,
  periodMonths,
  showMoney,
  readOnly,
  storageKey,
  serverError,
}: HrCostItemsEditorProps) {
  const columns = useMemo(() => buildCostItemColumns(showMoney, readOnly), [showMoney, readOnly])

  const ctx: HrCostItemCellContext = {
    items,
    groups,
    positions,
    monthChoices: periodMonths ?? ALL_MONTHS,
    readOnly,
    problems: new Map(items.map((i) => [i.code, listCostItemProblems(i, items, periodMonths ?? [])])),
    onPatch: (index, patch) =>
      onChange({ items: items.map((it, k) => (k === index ? { ...it, ...patch } : it)), lines }),
    onMethodChange: (index, method) =>
      onChange({ items: items.map((it, k) => (k === index ? changeCostItemMethod(it, method) : it)), lines }),
    onRename: (index, raw) => {
      const oldCode = items[index]?.code ?? ''
      const next = normalizeCostCode(raw)
      if (next === oldCode) return true
      const result = renameCostItemCode(items, lines, oldCode, raw)
      if (result.items[index]?.code === oldCode) return false
      onChange(result)
      return true
    },
    onMove: (index, delta) => onChange({ items: moveCostItem(items, index, delta), lines }),
    onRemove: (index) => onChange(removeCostItem(items, lines, items[index]?.code ?? '')),
  }

  return (
    <div className="space-y-2">
      {serverError && (
        <p className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/5 p-2 text-sm text-destructive">
          <AlertCircle className="mt-0.5 size-4 shrink-0" />
          <span>{serverError}</span>
        </p>
      )}
      <LinesTable<HrCostItem>
        columns={columns}
        rows={items}
        storageKey={storageKey}
        rowKey={(row, index) => `${index}-${row.id ?? 'new'}`}
        renderCell={(key, row, index) => <HrCostItemCell columnKey={key} item={row} index={index} ctx={ctx} />}
        title={`Khoản chi phí (${items.length})`}
        actions={
          !readOnly && (
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => onChange({ items: [...items, createEmptyCostItem(items, groups[0]?.id ?? 0)], lines })}
            >
              <Plus className="size-4" />
              Thêm khoản
            </Button>
          )
        }
        emptyMessage={
          readOnly ? 'Chưa có khoản chi phí nào.' : 'Chưa có khoản nào — bấm «Thêm khoản» để khai khoản đầu tiên.'
        }
      />
    </div>
  )
}
