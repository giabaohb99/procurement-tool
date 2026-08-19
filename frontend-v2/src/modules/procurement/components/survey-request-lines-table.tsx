import { Copy, Pencil, Trash2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import {
  usePurchaseRequestItemGroups,
  usePurchaseRequestUnits,
} from '../hooks/use-purchase-request-support'
import type { SurveyRequestLine } from '../types/survey-request-detail'
import { SurveyLineStateBadge } from './document-status-badge'

/** Dòng trống khi bấm "Thêm dòng". */
export const EMPTY_SURVEY_REQUEST_LINE: SurveyRequestLine = {
  item_group: '',
  requirement_detail: '',
  other_requirement: '',
  request_qty: 0,
  uom: '',
  proposed_price: 0,
  received_date: '',
  result_due_date: '',
  result_date: '',
  assignee: '',
  assignee_name: '',
  pr_id: 0,
  pr_code: '',
  is_completed: false,
  line_status: '',
  no_option: false,
  option_count: 0,
  has_chosen: false,
  progress_state: '',
  progress_tone: 'gray',
}

/** Mã giả cho mục "bỏ chọn NSTM" — Radix Select cấm dùng chuỗi rỗng làm value. */
const UNASSIGNED = '__unassigned__'
const EMPTY_CATALOG_VALUE = '__empty__'

interface SurveyRequestLinesTableProps {
  lines: SurveyRequestLine[]
  editing: boolean
  /** Cột nội bộ của thu mua (ngày tiếp nhận, NSTM) — người yêu cầu không thấy. */
  showNstmColumns: boolean
  /** Cột tiến độ dòng: phiếu chưa lưu thì chưa có gì để hiện. */
  showStatus: boolean
  canAssignNstm: boolean
  /** NSTM chọn được — hiện TÊN nhưng lưu MÃ nhân sự. */
  purchasers: { code: string; name: string }[]
  onChange: (lines: SurveyRequestLine[]) => void
  onOpenDetail: (index: number) => void
  /** Đổi NSTM ngay trên bảng — trang tự ghi xuống server, không chờ nút Lưu. */
  onAssigneeChange: (line: SurveyRequestLine, assignee: string) => void
  /**
   * Xóa / nhân bản dòng làm lệch chỉ số của mọi dòng phía sau. Trang đang giữ hộ
   * hình của dòng chưa lưu theo chỉ số nên phải biết chỗ vừa đổi mà dời khóa.
   */
  onLineRemoved?: (index: number) => void
  onLineDuplicated?: (index: number) => void
}

/**
 * Bảng "Danh sách sản phẩm cần khảo sát".
 *
 * Cột trạng thái đọc thẳng `progress_state` / `progress_tone` của backend
 * (CR-077) — đừng suy lại từ `option_count` hay `line_status` ở đây.
 */
export function SurveyRequestLinesTable({
  lines,
  editing,
  showNstmColumns,
  showStatus,
  canAssignNstm,
  purchasers,
  onChange,
  onOpenDetail,
  onAssigneeChange,
  onLineRemoved,
  onLineDuplicated,
}: SurveyRequestLinesTableProps) {
  const units = usePurchaseRequestUnits(editing)
  const itemGroups = usePurchaseRequestItemGroups(editing)

  function patch(index: number, changes: Partial<SurveyRequestLine>) {
    onChange(lines.map((line, i) => (i === index ? { ...line, ...changes } : line)))
  }

  /** Nhân bản dòng: bỏ mọi dấu vết của bản gốc để backend hiểu là dòng mới. */
  function duplicate(index: number) {
    const source = lines[index]
    if (!source) return
    const copy: SurveyRequestLine = {
      ...source,
      id: 0,
      received_date: '',
      result_date: '',
      assignee: '',
      assignee_name: '',
      pr_id: 0,
      pr_code: '',
      is_completed: false,
      line_status: '',
      no_option: false,
      option_count: 0,
      has_chosen: false,
      progress_state: '',
      progress_tone: 'gray',
    }
    onChange([...lines.slice(0, index + 1), copy, ...lines.slice(index + 1)])
    onLineDuplicated?.(index)
  }

  function remove(index: number) {
    onChange(lines.filter((_, i) => i !== index))
    onLineRemoved?.(index)
  }

  const columnCount = 8 + (showNstmColumns ? 2 : 0) + (showStatus ? 1 : 0)

  return (
    <div className="overflow-x-auto rounded-lg border">
      <Table className="[&_td]:border-r [&_td:last-child]:border-r-0 [&_th]:border-r [&_th:last-child]:border-r-0">
        <TableHeader className="bg-muted">
          <TableRow className="bg-muted">
            <TableHead className="w-[42px] text-center">No.</TableHead>
            {showNstmColumns && (
              <TableHead className="w-[110px]" title="Thời điểm NSTM nhận dòng này">
                Ngày tiếp nhận
              </TableHead>
            )}
            <TableHead className="w-[130px]">Ngày YC trả KQ</TableHead>
            <TableHead className="w-[160px]">Phân loại</TableHead>
            <TableHead className="min-w-56">Chi tiết thông số</TableHead>
            <TableHead className="w-[90px] text-right">SL dự kiến</TableHead>
            <TableHead className="w-[100px]">ĐVT</TableHead>
            <TableHead className="w-[120px] text-right">Giá đề xuất</TableHead>
            {showNstmColumns && <TableHead className="w-[170px]">Nhân sự phụ trách</TableHead>}
            {showStatus && <TableHead className="w-[130px] text-center">Trạng thái</TableHead>}
            <TableHead className="w-[92px] text-center">Thao tác</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {lines.length === 0 && (
            <TableRow>
              <TableCell colSpan={columnCount} className="py-10 text-center text-muted-foreground">
                Chưa có dòng nào — nhấn "Thêm dòng" để bắt đầu
              </TableCell>
            </TableRow>
          )}

          {lines.map((line, index) => (
            <TableRow key={line.id || `new-${index}`} className="bg-card hover:bg-muted">
              <TableCell className="text-center text-muted-foreground">{index + 1}</TableCell>

              {showNstmColumns && (
                <TableCell className="text-muted-foreground">
                  {formatDate(line.received_date) || '—'}
                </TableCell>
              )}

              <TableCell>
                {editing ? (
                  <DatePicker
                    size="sm"
                    value={line.result_due_date || ''}
                    onChange={(value) => patch(index, { result_due_date: value })}
                  />
                ) : (
                  formatDate(line.result_due_date) || '—'
                )}
              </TableCell>

              <TableCell>
                {editing ? (
                  <CatalogSelect
                    value={line.item_group}
                    placeholder="-- Phân loại --"
                    options={(itemGroups.data?.items ?? []).map((group) => ({
                      value: group.name,
                      label: group.name,
                    }))}
                    onChange={(value) => patch(index, { item_group: value })}
                  />
                ) : (
                  <span className="block truncate" title={line.item_group}>
                    {line.item_group || '—'}
                  </span>
                )}
              </TableCell>

              <TableCell>
                {editing ? (
                  <Input
                    value={line.requirement_detail}
                    placeholder="Thông số / chất lượng cần khảo sát"
                    onChange={(event) => patch(index, { requirement_detail: event.target.value })}
                  />
                ) : (
                  <span className="block truncate" title={line.requirement_detail}>
                    {line.requirement_detail || '—'}
                  </span>
                )}
              </TableCell>

              <TableCell className="text-right">
                {editing ? (
                  <Input
                    className="text-right"
                    type="number"
                    min={0}
                    step="0.001"
                    value={line.request_qty || ''}
                    onChange={(event) => patch(index, { request_qty: Number(event.target.value) })}
                  />
                ) : (
                  <span className="tabular-nums">{formatQuantity(line.request_qty) || '—'}</span>
                )}
              </TableCell>

              <TableCell>
                {editing ? (
                  <CatalogSelect
                    value={line.uom}
                    placeholder="-- ĐVT --"
                    options={(units.data?.items ?? []).map((unit) => ({
                      value: unit.name,
                      label: unit.name,
                    }))}
                    onChange={(value) => patch(index, { uom: value })}
                  />
                ) : (
                  line.uom || '—'
                )}
              </TableCell>

              <TableCell className="text-right">
                {editing ? (
                  <Input
                    className="text-right"
                    type="number"
                    min={0}
                    // Đơn giá giữ tới 4 số lẻ như mọi đơn giá trong hệ.
                    step="0.0001"
                    value={line.proposed_price || ''}
                    onChange={(event) =>
                      patch(index, { proposed_price: Number(event.target.value) })
                    }
                  />
                ) : (
                  <span className="tabular-nums">{formatUnitPrice(line.proposed_price) || '—'}</span>
                )}
              </TableCell>

              {showNstmColumns && (
                <TableCell>
                  {/* Dòng chưa lưu thì chưa có id để gán — chờ bấm Lưu đã. */}
                  {canAssignNstm && line.id ? (
                    <Select
                      value={line.assignee || undefined}
                      onValueChange={(value) => {
                        const assignee = value === UNASSIGNED ? '' : value
                        patch(index, { assignee })
                        onAssigneeChange(line, assignee)
                      }}
                    >
                      <SelectTrigger size="sm" className="w-full">
                        <SelectValue placeholder="Chọn NSTM" />
                      </SelectTrigger>
                      <SelectContent>
                        {line.assignee && (
                          <SelectItem value={UNASSIGNED} className="text-muted-foreground">
                            — Bỏ chọn —
                          </SelectItem>
                        )}
                        {purchasers.map((purchaser) => (
                          <SelectItem key={purchaser.code} value={purchaser.code}>
                            {purchaser.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  ) : (
                    line.assignee_name ||
                    purchasers.find((purchaser) => purchaser.code === line.assignee)?.name ||
                    line.assignee ||
                    '—'
                  )}
                </TableCell>
              )}

              {showStatus && (
                <TableCell className="text-center">
                  <SurveyLineStateBadge state={line.progress_state} tone={line.progress_tone} />
                </TableCell>
              )}

              <TableCell>
                <div className="flex items-center justify-center gap-1">
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    title="Chi tiết dòng"
                    onClick={() => onOpenDetail(index)}
                  >
                    <Pencil />
                  </Button>
                  {editing && (
                    <>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        title="Nhân bản dòng"
                        onClick={() => duplicate(index)}
                      >
                        <Copy />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        className="text-destructive hover:text-destructive"
                        title="Xóa dòng"
                        onClick={() => remove(index)}
                      >
                        <Trash2 />
                      </Button>
                    </>
                  )}
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

function CatalogSelect({
  value,
  placeholder,
  options,
  onChange,
}: {
  value: string
  placeholder: string
  options: { value: string; label: string }[]
  onChange: (value: string) => void
}) {
  return (
    <Select
      value={value || EMPTY_CATALOG_VALUE}
      onValueChange={(next) => onChange(next === EMPTY_CATALOG_VALUE ? '' : next)}
    >
      <SelectTrigger size="sm" className="w-full">
        <SelectValue />
      </SelectTrigger>
      <SelectContent position="popper" align="start">
        <SelectItem value={EMPTY_CATALOG_VALUE}>{placeholder}</SelectItem>
        {options.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
