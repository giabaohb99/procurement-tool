import { Copy, FilePlus2, Pencil, Trash2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { cn } from '@/shared/utils/cn'
import { formatMoney } from '@/shared/utils/format-money'
import type { SurveyCatalog } from '../helpers/survey-catalog'
import { rowAmount } from '../helpers/survey-line'
import {
  LINE_APPROVE_NEED_MORE,
  SURVEY_TABLE_MIN_WIDTH,
  columnsOf,
  coreKeysOf,
  type SurveyLine,
  type SurveyTable,
} from '../types/survey-detail'
import { SurveyLineField } from './survey-line-field'

interface SurveyLinesTableProps {
  table: SurveyTable
  lines: SurveyLine[]
  /** Chế độ RÚT GỌN: chỉ hiện cột cốt lõi, phần còn lại xem ở popup chi tiết dòng. */
  compact: boolean
  editable: boolean
  approveEditable: boolean
  /** Khóa `${table}-${index}-${key}` của ô còn thiếu, tô đỏ sau khi bấm Gửi duyệt. */
  invalid: Set<string>
  catalog: SurveyCatalog
  /** Chỉ số dòng đang tick để xóa hàng loạt. */
  selected: Set<number>
  /** Được phép mở popup "Bổ sung" cho dòng bị TP/QL báo thiếu thông tin. */
  canFill: boolean
  onSelectedChange: (next: Set<number>) => void
  onChangeLine: (index: number, changes: Partial<SurveyLine>) => void
  onOpenLine: (index: number, mode: 'edit' | 'fill') => void
  onDuplicate: (index: number) => void
  onRemove: (index: number) => void
}

/**
 * Bảng dòng của phiếu khảo sát — 27 cột (NCC) hoặc 30 cột (SP).
 *
 * HỢP ĐỒNG HIỂN THỊ (CR-090), đừng phá khi sửa file này:
 * - MỌI ô chữ phải xuống dòng, cả ô sửa được lẫn ô chỉ đọc. Bảng chạy
 *   `table-fixed` nên `overflow-wrap` là thứ duy nhất giữ chữ nằm trong ô.
 * - KHÔNG nới `SURVEY_TABLE_MIN_WIDTH` để né chữ tràn — nới chỉ làm thanh cuộn
 *   ngang dài thêm, chữ vẫn tràn ở màn hẹp.
 * - Ô nằm trong `<td>` phải `align-top`: dòng cao thấp khác nhau, canh giữa là
 *   mỗi ô một cao độ, mắt không dò được theo hàng.
 */
export function SurveyLinesTable({
  table,
  lines,
  compact,
  editable,
  approveEditable,
  invalid,
  catalog,
  selected,
  canFill,
  onSelectedChange,
  onChangeLine,
  onOpenLine,
  onDuplicate,
  onRemove,
}: SurveyLinesTableProps) {
  const coreKeys = coreKeysOf(table)
  const columns = columnsOf(table).filter((column) => !compact || coreKeys.includes(column.key))
  const columnCount = columns.length + 2 + (editable ? 1 : 0)
  const allChecked = lines.length > 0 && selected.size === lines.length

  function toggleRow(index: number) {
    const next = new Set(selected)
    if (next.has(index)) next.delete(index)
    else next.add(index)
    onSelectedChange(next)
  }

  return (
    <Table
      containerClassName="rounded-lg border"
      className={cn(
        'table-fixed [&_td]:border-r [&_td]:p-1.5 [&_td]:align-top [&_td:last-child]:border-r-0',
        '[&_th]:border-r [&_th]:p-2 [&_th:last-child]:border-r-0',
      )}
      style={{ minWidth: compact ? undefined : SURVEY_TABLE_MIN_WIDTH[table] }}
    >
      <colgroup>
        {editable && <col style={{ width: 40 }} />}
        <col style={{ width: 44 }} />
        {columns.map((column) => (
          <col key={column.key} style={{ width: column.width }} />
        ))}
        <col style={{ width: 100 }} />
      </colgroup>

      <TableHeader className="bg-muted">
        <TableRow>
          {editable && (
            <TableHead>
              <Checkbox
                checked={allChecked}
                aria-label="Chọn tất cả dòng"
                onCheckedChange={(next) =>
                  onSelectedChange(next === true ? new Set(lines.map((_, i) => i)) : new Set())
                }
              />
            </TableHead>
          )}
          <TableHead className="text-center">#</TableHead>
          {columns.map((column) => (
            <TableHead key={column.key} className="whitespace-normal leading-snug">
              {column.label}
            </TableHead>
          ))}
          <TableHead className="text-center">Hành động</TableHead>
        </TableRow>
      </TableHeader>

      <TableBody>
        {lines.length === 0 && (
          <TableRow>
            <TableCell colSpan={columnCount} className="py-6 text-center text-muted-foreground">
              Chưa có dòng nào.
            </TableCell>
          </TableRow>
        )}

        {lines.map((line, index) => {
          // Dòng bị TP/QL trả về "Thiếu thông tin" vẫn phải điền thêm được kể cả
          // khi phiếu đã gửi — đó chính là việc TP/QL vừa yêu cầu.
          const needMore = line.line_approve === LINE_APPROVE_NEED_MORE
          const fillable = !editable && canFill && needMore

          return (
            <TableRow key={line.id ?? `new-${index}`}>
              {editable && (
                <TableCell>
                  <Checkbox
                    checked={selected.has(index)}
                    aria-label={`Chọn dòng ${index + 1}`}
                    onCheckedChange={() => toggleRow(index)}
                  />
                </TableCell>
              )}
              <TableCell className="pt-3 text-center text-muted-foreground">{index + 1}</TableCell>

              {columns.map((column) => (
                <TableCell key={column.key}>
                  <SurveyLineField
                    field={column}
                    line={line}
                    variant="cell"
                    editable={editable}
                    approveEditable={approveEditable}
                    invalid={invalid.has(`${table}-${index}-${column.key}`)}
                    catalog={catalog}
                    onChange={(changes) => onChangeLine(index, changes)}
                  />
                </TableCell>
              ))}

              <TableCell>
                <div className="flex items-center justify-center gap-0.5">
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    title="Mở chi tiết dòng"
                    onClick={() => onOpenLine(index, 'edit')}
                  >
                    <Pencil />
                  </Button>
                  {fillable && (
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      title="Bổ sung thông tin theo yêu cầu TP/QL"
                      onClick={() => onOpenLine(index, 'fill')}
                    >
                      <FilePlus2 />
                    </Button>
                  )}
                  {editable && (
                    <>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        title="Nhân bản dòng"
                        onClick={() => onDuplicate(index)}
                      >
                        <Copy />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        title="Xóa dòng"
                        className="text-destructive hover:text-destructive"
                        onClick={() => onRemove(index)}
                      >
                        <Trash2 />
                      </Button>
                    </>
                  )}
                </div>
              </TableCell>
            </TableRow>
          )
        })}
      </TableBody>

      {table === 'product' && lines.length > 0 && (
        <TableFooter>
          <TableRow>
            <TableCell colSpan={columnCount - 1} className="text-right font-medium">
              Tổng thành tiền
            </TableCell>
            <TableCell className="text-right font-semibold">
              {formatMoney(lines.reduce((sum, line) => sum + rowAmount(line), 0))}
            </TableCell>
          </TableRow>
        </TableFooter>
      )}
    </Table>
  )
}
