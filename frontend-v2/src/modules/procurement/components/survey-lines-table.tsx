import { useMemo, type ReactNode } from 'react'
import { Copy, FilePlus2, Pencil, Trash2 } from 'lucide-react'

import { LinesTable } from '@/shared/data-table/lines-table'
import type { LinesTableColumn } from '@/shared/data-table/types'
import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { formatMoney } from '@/shared/utils/format-money'
import type { SurveyCatalog } from '../helpers/survey-catalog'
import { rowAmount } from '../helpers/survey-line'
import {
  LINE_APPROVE_NEED_MORE,
  columnsOf,
  coreKeysOf,
  type SurveyLine,
  type SurveyTable,
} from '../types/survey-detail'
import { SurveyLineField } from './survey-line-field'

/** Ba cột khung: tick chọn, số thứ tự, nút thao tác — không phải cột dữ liệu. */
const SELECT_KEY = 'select'
const NO_KEY = 'no'
const ACTION_KEY = 'action'

/**
 * Cột định danh ghim sẵn bên trái. Bảng dài 27–30 cột, cuộn tới cột "Chính sách
 * công nợ" mà không thấy đang xem NCC nào thì cuộn cũng bằng thừa.
 */
const IDENTITY_KEY = 'supplier_code'

/** Mỗi bảng nhớ bố cục riêng — hai bảng khác hẳn nhau về cột. */
const STORAGE_KEY: Record<SurveyTable, string> = {
  supplier: 'survey-supplier-lines',
  product: 'survey-product-lines',
}

interface SurveyLinesTableProps {
  table: SurveyTable
  lines: SurveyLine[]
  editable: boolean
  approveEditable: boolean
  /** Khóa `${table}-${index}-${key}` của ô còn thiếu, tô đỏ sau khi bấm Gửi duyệt. */
  invalid: Set<string>
  catalog: SurveyCatalog
  /** Chỉ số dòng đang tick để xóa hàng loạt. */
  selected: Set<number>
  /** Được phép mở popup "Bổ sung" cho dòng bị TP/QL báo thiếu thông tin. */
  canFill: boolean
  /** Nút riêng của trang (Thêm dòng, Thêm nhiều, Xóa dòng đã chọn). */
  actions?: ReactNode
  onSelectedChange: (next: Set<number>) => void
  onChangeLine: (index: number, changes: Partial<SurveyLine>) => void
  onOpenLine: (index: number, mode: 'edit' | 'fill') => void
  onDuplicate: (index: number) => void
  onRemove: (index: number) => void
}

/**
 * Bảng dòng của phiếu khảo sát — 27 cột (NCC) hoặc 30 cột (SP), dựng trên
 * `LinesTable` nên có sẵn menu "Cột" (bật/tắt từng cột), ghim, kéo thả đổi thứ
 * tự, kéo giãn và nhớ bố cục vào localStorage.
 *
 * CR-103: trước đây bảng này tự dựng `<table>` nên chỉ có đúng hai nấc rút gọn /
 * đầy đủ do trang điều khiển — muốn xem thêm một cột là phải bung cả 30 cột.
 * Nay nhóm cột phụ khai bằng `compactHidden`: nút "Bảng đầy đủ" vẫn bật/tắt cả
 * nhóm, còn menu "Cột" cho chọn lẻ từng cột.
 *
 * HỢP ĐỒNG HIỂN THỊ (CR-090), đừng phá khi sửa file này:
 * - MỌI ô chữ phải xuống dòng, cả ô sửa được lẫn ô chỉ đọc. Bảng chạy
 *   `table-fixed` nên `overflow-wrap` là thứ duy nhất giữ chữ nằm trong ô.
 * - KHÔNG nới bề rộng cột để né chữ tràn — nới chỉ làm thanh cuộn ngang dài
 *   thêm, chữ vẫn tràn ở màn hẹp. Cần rộng thì người dùng tự kéo, bảng nhớ hộ.
 * - Ô phải `align-top`: dòng cao thấp khác nhau, canh giữa là mỗi ô một cao độ,
 *   mắt không dò được theo hàng.
 */
export function SurveyLinesTable({
  table,
  lines,
  editable,
  approveEditable,
  invalid,
  catalog,
  selected,
  canFill,
  actions,
  onSelectedChange,
  onChangeLine,
  onOpenLine,
  onDuplicate,
  onRemove,
}: SurveyLinesTableProps) {
  const fieldByKey = useMemo(
    () => new Map(columnsOf(table).map((column) => [column.key, column])),
    [table],
  )

  const columns = useMemo<LinesTableColumn[]>(() => {
    const coreKeys = coreKeysOf(table)
    const dataColumns = columnsOf(table).map<LinesTableColumn>((column) => ({
      key: column.key,
      header: column.label,
      width: column.width,
      minWidth: 70,
      compactHidden: !coreKeys.includes(column.key),
      defaultPinned: column.key === IDENTITY_KEY,
    }))

    const selectColumn: LinesTableColumn[] = editable
      ? [
          {
            key: SELECT_KEY,
            header: 'Chọn',
            width: 48,
            minWidth: 44,
            align: 'center',
            hideable: false,
            defaultPinned: true,
          },
        ]
      : []

    return [
      ...selectColumn,
      {
        key: NO_KEY,
        header: 'No.',
        width: 48,
        minWidth: 40,
        align: 'center',
        hideable: false,
        defaultPinned: true,
      },
      ...dataColumns,
      {
        key: ACTION_KEY,
        header: 'Thao tác',
        width: 104,
        minWidth: 80,
        align: 'center',
        hideable: false,
      },
    ]
  }, [table, editable])

  const allChecked = lines.length > 0 && selected.size === lines.length

  function toggleRow(index: number) {
    const next = new Set(selected)
    if (next.has(index)) next.delete(index)
    else next.add(index)
    onSelectedChange(next)
  }

  function renderCell(key: string, line: SurveyLine, index: number) {
    if (key === SELECT_KEY) {
      return (
        <Checkbox
          checked={selected.has(index)}
          aria-label={`Chọn dòng ${index + 1}`}
          onCheckedChange={() => toggleRow(index)}
        />
      )
    }

    if (key === NO_KEY) return <span className="text-muted-foreground">{index + 1}</span>

    if (key === ACTION_KEY) {
      // Dòng bị TP/QL trả về "Thiếu thông tin" vẫn phải điền thêm được kể cả
      // khi phiếu đã gửi — đó chính là việc TP/QL vừa yêu cầu.
      const fillable = !editable && canFill && line.line_approve === LINE_APPROVE_NEED_MORE

      return (
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
      )
    }

    const field = fieldByKey.get(key)
    if (!field) return null

    return (
      <SurveyLineField
        field={field}
        line={line}
        variant="cell"
        editable={editable}
        approveEditable={approveEditable}
        invalid={invalid.has(`${table}-${index}-${key}`)}
        catalog={catalog}
        onChange={(changes) => onChangeLine(index, changes)}
      />
    )
  }

  return (
    <div className="space-y-3">
      <LinesTable
        columns={columns}
        rows={lines}
        storageKey={STORAGE_KEY[table]}
        rowKey={(line, index) => line.id ?? `new-${index}`}
        renderCell={renderCell}
        defaultCompact
        title={`${lines.length} dòng`}
        actions={
          <>
            {editable && lines.length > 0 && (
              <label className="flex cursor-pointer items-center gap-1.5 text-xs font-normal text-muted-foreground">
                <Checkbox
                  checked={allChecked}
                  aria-label="Chọn tất cả dòng"
                  onCheckedChange={(next) =>
                    onSelectedChange(
                      next === true ? new Set(lines.map((_, index) => index)) : new Set(),
                    )
                  }
                />
                Chọn tất cả
              </label>
            )}
            {actions}
          </>
        }
        emptyMessage="Chưa có dòng nào."
        cellClassName={(key) =>
          key === SELECT_KEY || key === NO_KEY ? 'align-top pt-3' : 'align-top'
        }
      />

      {/* `LinesTable` không có `<tfoot>` (cột ẩn/hiện được thì `colSpan` vô
          nghĩa) — tổng tiền đưa xuống dưới bảng, đọc vẫn đúng chỗ. */}
      {table === 'product' && lines.length > 0 && (
        <div className="flex items-center justify-end gap-4 rounded-lg border bg-muted/40 px-4 py-2 text-sm">
          <span className="font-medium">Tổng thành tiền</span>
          <span className="font-semibold tabular-nums">
            {formatMoney(lines.reduce((sum, line) => sum + rowAmount(line), 0))}
          </span>
        </div>
      )}
    </div>
  )
}
