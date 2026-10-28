import { Plus } from 'lucide-react'
import { useMemo, useState, type ReactNode } from 'react'

import { LinesTable } from '@/shared/data-table/lines-table'
import { Button } from '@/shared/ui/button'
import { SearchSelect } from '@/shared/ui/search-select'
import { buildHeadcountPlanLineColumns } from '../config/headcount-plan-line-columns'
import {
  NO_POSITION_ID,
  NO_POSITION_LABEL,
  type HeadcountPlanLine,
  type HeadcountPlanPeriod,
  type HeadcountPlanPositionStat,
} from '../types/headcount-plan'
import type { HrCostItem } from '../types/hr-cost'
import { countCurrentForLine } from '../utils/headcount-plan-draft'
import { HeadcountPlanLineCell, type HeadcountPlanLineCellContext } from './headcount-plan-line-cell'

interface HeadcountPlanLinesEditorProps {
  lines: HeadcountPlanLine[]
  periods: readonly HeadcountPlanPeriod[]
  periodType: number
  items: readonly HrCostItem[]
  stats: readonly HeadcountPlanPositionStat[]
  positions: readonly { id: number; name: string }[]
  showMoney: boolean
  readOnly: boolean
  onChange: (lines: HeadcountPlanLine[]) => void
  onAdd: (positionId: number, positionName: string) => void
  /** Nút phụ trên đầu bảng (nhập CSV dòng vị trí). */
  extraActions?: ReactNode
}

/**
 * Khối 3 — ĐỊNH BIÊN THEO VỊ TRÍ (tài liệu 06 §2.3). Số cột định biên đổi theo loại kỳ, mỗi khoản
 * «nhập theo vị trí» mọc một cột số tiền. «Đang có» + gợi ý bình quân lấy từ `/position-stats`.
 */
export function HeadcountPlanLinesEditor({
  lines,
  periods,
  periodType,
  items,
  stats,
  positions,
  showMoney,
  readOnly,
  onChange,
  onAdd,
  extraActions,
}: HeadcountPlanLinesEditorProps) {
  const [picked, setPicked] = useState('')
  const columns = useMemo(
    () => buildHeadcountPlanLineColumns({ periods, items, showMoney, readOnly }),
    [periods, items, showMoney, readOnly],
  )
  const used = new Set(lines.map((l) => l.position_id))
  const options = positions
    .filter((p) => !used.has(p.id))
    .map((p) => ({ value: String(p.id), label: p.name }))

  const ctx: HeadcountPlanLineCellContext = {
    items,
    stats,
    currentCounts: lines.map((l) => countCurrentForLine(l, lines, stats)),
    showMoney,
    readOnly,
    onPatch: (index, patch) => onChange(lines.map((l, k) => (k === index ? { ...l, ...patch } : l))),
    onRemove: (index) => onChange(lines.filter((_, k) => k !== index)),
  }

  const addPicked = () => {
    const id = Number(picked)
    const position = positions.find((p) => p.id === id)
    if (!position) return
    onAdd(position.id, position.name)
    setPicked('')
  }

  return (
    <LinesTable<HeadcountPlanLine>
      columns={columns}
      rows={lines}
      //  Mỗi loại kỳ một bố cục: số cột định biên khác nhau, nhớ chung một khóa là cột của Năm (4 cột)
      //  và của Quý (3 cột) đè thứ tự của nhau.
      storageKey={`hr.headcount-plan.lines.p${periodType}`}
      rowKey={(row) => `p${row.position_id}`}
      renderCell={(key, row, index) => <HeadcountPlanLineCell columnKey={key} line={row} index={index} ctx={ctx} />}
      title={`Định biên theo vị trí (${lines.length})`}
      actions={
        <div className="flex flex-wrap items-center gap-2">
          {!readOnly && (
            <>
              <SearchSelect
                value={picked}
                onChange={setPicked}
                options={options}
                placeholder="Chọn vị trí để thêm"
                searchPlaceholder="Tìm chức vụ…"
                emptyMessage="Mọi chức vụ đã có dòng."
                size="sm"
                className="w-56"
              />
              <Button type="button" size="sm" variant="outline" disabled={!picked} onClick={addPicked}>
                <Plus className="size-4" />
                Thêm vị trí
              </Button>
              {!used.has(NO_POSITION_ID) && (
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  onClick={() => onAdd(NO_POSITION_ID, NO_POSITION_LABEL)}
                  title="Cho ai chỉ muốn nhập tổng người của phòng, không chia theo chức vụ"
                >
                  <Plus className="size-4" />
                  Dòng «{NO_POSITION_LABEL}»
                </Button>
              )}
            </>
          )}
          {extraActions}
        </div>
      }
      emptyMessage={
        readOnly
          ? 'Kế hoạch chưa có dòng vị trí nào.'
          : 'Chưa có dòng nào — chọn một vị trí để thêm, hoặc thêm dòng «Không theo vị trí» nếu chỉ nhập tổng phòng.'
      }
    />
  )
}
