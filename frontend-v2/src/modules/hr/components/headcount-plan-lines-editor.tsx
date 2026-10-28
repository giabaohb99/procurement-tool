import { Plus } from 'lucide-react'

import { PLAN_PERIOD_TYPE_CODE } from '@/shared/constants/statuses'
import { Button } from '@/shared/ui/button'
import { Table, TableBody, TableHead, TableHeader, TableRow } from '@/shared/ui/table'
import {
  NO_POSITION_ID,
  NO_POSITION_LABEL,
  type HeadcountPlanLine,
  type HeadcountPlanPeriod,
  type HeadcountPlanPositionStat,
} from '../types/headcount-plan'
import type { HrCostItem } from '../types/hr-cost'
import { countCurrentForLine } from '../utils/headcount-plan-draft'
import { describePerHeadColumn } from '../utils/hr-cost-item-presets'
import { listPerPositionItems } from '../utils/hr-cost-item-rules'
import { HeadcountPlanLineRow } from './headcount-plan-line-row'
import { HeadcountPlanPositionPicker } from './headcount-plan-position-picker'

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
}

const EMPTY_HINT = 'Bấm Thêm vị trí. Ví dụ Kế toán viên: hiện có 4, cần 5 người từ Q3, lương 12.000.000.'

/**
 * Khối ① NGƯỜI VÀ LƯƠNG (duoc-CR-690, bố cục đại ca chốt 28/10/2026): Vị trí · Hiện có · Cần có từng kỳ
 * con · Cần tuyển · Lương/người · Phụ cấp/người (+ cột cho khoản hằng tháng khác của dữ liệu cũ).
 *
 * Bảng thường, KHÔNG dùng `LinesTable`: đại ca chốt bỏ thanh «Bảng đầy đủ / Vừa nội dung / Cột» ở bảng
 * này; cột đã gọn để vừa màn ≥1280 không cuộn ngang, màn hẹp thì khung bảng tự cuộn. Không được xem tiền
 * thì KHÔNG dựng cột tiền (một cột toàn ô trống đọc ra «chưa ai nhập lương»).
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
}: HeadcountPlanLinesEditorProps) {
  const moneyItems = showMoney ? listPerPositionItems(items.filter((i) => !i.excluded)) : []
  const used = new Set(lines.map((l) => l.position_id))
  const fillLabel = periodType === PLAN_PERIOD_TYPE_CODE.YEAR ? 'Giống nhau cả năm' : 'Giống nhau cả kỳ'
  const patchLine = (index: number, patch: Partial<HeadcountPlanLine>) =>
    onChange(lines.map((l, k) => (k === index ? { ...l, ...patch } : l)))

  return (
    <div className="space-y-2">
      <div className="rounded-md border">
        <Table className="min-w-[720px]">
          <TableHeader>
            <TableRow>
              <TableHead rowSpan={2} className="min-w-40 align-bottom">
                Vị trí
              </TableHead>
              <TableHead rowSpan={2} className="w-16 text-right align-bottom" title="Số người đang làm ở vị trí này">
                Hiện có
              </TableHead>
              <TableHead colSpan={periods.length} className="h-7 border-b text-center">
                Cần có
              </TableHead>
              <TableHead rowSpan={2} className="w-20 text-right align-bottom" title="Cần có ở kỳ cuối trừ hiện có">
                Cần tuyển
              </TableHead>
              {moneyItems.map((item) => (
                <TableHead key={item.code} rowSpan={2} className="w-36 text-right align-bottom whitespace-normal">
                  {describePerHeadColumn(item)}
                </TableHead>
              ))}
              {!readOnly && <TableHead rowSpan={2} className="w-10" aria-label="Xóa dòng" />}
            </TableRow>
            <TableRow>
              {periods.map((p) => (
                <TableHead key={p.key} className="h-7 w-16 text-right">
                  {p.label}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {lines.map((line, index) => (
              <HeadcountPlanLineRow
                key={`p${line.position_id}`}
                line={line}
                periods={periods}
                moneyItems={moneyItems}
                current={countCurrentForLine(line, lines, stats)}
                stat={stats.find((s) => s.position_id === line.position_id)}
                fillLabel={fillLabel}
                readOnly={readOnly}
                onPatch={(patch) => patchLine(index, patch)}
                onRemove={() => onChange(lines.filter((_, k) => k !== index))}
              />
            ))}
          </TableBody>
        </Table>
        {lines.length === 0 && (
          <p className="border-t p-4 text-center text-sm text-muted-foreground">
            {readOnly ? 'Kế hoạch chưa có vị trí nào.' : EMPTY_HINT}
          </p>
        )}
      </div>
      {!readOnly && (
        <div className="flex flex-wrap items-center gap-2">
          <HeadcountPlanPositionPicker options={positions.filter((p) => !used.has(p.id))} onPick={onAdd} />
          {!used.has(NO_POSITION_ID) && (
            <Button
              type="button"
              size="sm"
              variant="ghost"
              title="Dùng khi không chia theo vị trí — chỉ nhập tổng số người của phòng"
              onClick={() => onAdd(NO_POSITION_ID, NO_POSITION_LABEL)}
            >
              <Plus className="size-4" />
              Nhập tổng cả phòng
            </Button>
          )}
        </div>
      )}
    </div>
  )
}
