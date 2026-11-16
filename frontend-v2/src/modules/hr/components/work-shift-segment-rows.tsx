import { Clock, Plus, Trash2 } from 'lucide-react'
import { useRef } from 'react'

import { Button } from '@/shared/ui/button'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { formatHourLabel, MAX_SEGMENTS_PER_DAY } from '../utils/work-shift-hours'
import {
  nextFreeHourBlock,
  rowHours,
  withStartHour,
  type ShiftRow,
  type ShiftRowsValidation,
} from '../utils/work-shift-rows'
import { WorkShiftHourRangeInput } from './work-shift-hour-range-input'

interface WorkShiftSegmentRowsProps {
  rows: ShiftRow[]
  onChange: (next: ShiftRow[]) => void
  validation: ShiftRowsValidation
  readOnly?: boolean
}

/**
 * Danh sách KHUNG GIỜ của hộp xếp ca (duoc-CR-761, bản làm lại 16/11/2026), không khung viền bao ngoài. Mỗi dòng là
 * lưới cột thẳng hàng: [số tròn màu ca] [Từ – Đến] [x giờ] … [nút thùng rác]; điện thoại thì "x giờ" xuống dưới ô
 * ghép. Lỗi (Đến ≤ Từ, trùng giờ khung khác) hiện ngay dưới dòng sai. Không sắp lại khi đang sửa — chỉ sắp lúc lưu.
 * Cuối danh sách là nút nét đứt "+ Thêm khung giờ" (tắt khi đủ 12 khung / hết giờ trống, kèm câu lý do).
 */
export function WorkShiftSegmentRows({ rows, onChange, validation, readOnly = false }: WorkShiftSegmentRowsProps) {
  //  Khóa cho dòng thêm mới: tăng trong trình xử lý sự kiện (không trong lúc render).
  const counter = useRef(0)
  const next = nextFreeHourBlock(rows)

  const update = (id: string, patch: (row: ShiftRow) => ShiftRow) =>
    onChange(rows.map((row) => (row.id === id ? patch(row) : row)))

  const add = () => {
    if (!next) return
    counter.current += 1
    onChange([...rows, { id: `n${counter.current}`, ...next }])
  }

  if (readOnly) {
    //  Chỉ xem: danh sách chữ thường (bôi đen / copy được) — không ô chọn bị tắt, không khung xám giống ô nhập.
    if (rows.length === 0) return <p className="text-sm text-muted-foreground">Nghỉ cả ngày — không có khung giờ.</p>
    return (
      <ul aria-label="Các khung giờ" className="divide-y rounded-md border">
        {rows.map((row) => (
          <li key={row.id} className="flex items-center gap-2 px-3 py-2 text-sm">
            <Clock aria-hidden className="size-4 shrink-0 text-muted-foreground" />
            <span className="font-medium tabular-nums">
              {formatHourLabel(row.start)} – {formatHourLabel(row.end)}
            </span>
            <span className="ml-auto text-muted-foreground tabular-nums">{rowHours(row)} giờ</span>
          </li>
        ))}
      </ul>
    )
  }

  const addBlockedReason =
    rows.length >= MAX_SEGMENTS_PER_DAY
      ? `Đã đủ ${MAX_SEGMENTS_PER_DAY} khung giờ — tối đa một ngày.`
      : 'Không còn giờ trống trong ngày để thêm khung.'

  return (
    <div className="space-y-2">
      {rows.length === 0 && (
        <p className="text-sm text-muted-foreground">Chưa có khung giờ nào — thêm khung hoặc chọn mẫu nhanh.</p>
      )}
      {rows.length > 0 && (
        <ol aria-label="Các khung giờ" className="space-y-2">
          {rows.map((row, i) => {
            const error = validation.rowErrors[row.id]
            const errorId = `shift-row-error-${row.id}`
            const label = `Khung ${i + 1}`
            return (
              <li
                key={row.id}
                className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-x-2 gap-y-0.5 md:grid-cols-[auto_auto_minmax(0,1fr)_auto] md:gap-x-3"
              >
                <span
                  aria-hidden
                  className="col-start-1 row-start-1 flex size-6 items-center justify-center rounded-full bg-shift text-xs font-semibold text-shift-foreground tabular-nums"
                >
                  {i + 1}
                </span>
                <div className="col-start-2 row-start-1 min-w-0">
                  <WorkShiftHourRangeInput
                    label={label}
                    start={row.start}
                    end={row.end}
                    invalid={Boolean(error)}
                    describedBy={error ? errorId : undefined}
                    onStartChange={(h) => update(row.id, (r) => withStartHour(r, h))}
                    onEndChange={(h) => update(row.id, (r) => ({ ...r, end: h }))}
                  />
                </div>
                <span className="col-start-2 row-start-2 text-xs whitespace-nowrap text-muted-foreground tabular-nums md:col-start-3 md:row-start-1 md:text-sm">
                  {rowHours(row)} giờ
                </span>
                <div className="col-start-3 row-start-1 justify-self-end md:col-start-4">
                  <IconTooltip label="Xóa khung">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      className="text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                      aria-label={`Xóa ${label.toLowerCase()}`}
                      onClick={() => onChange(rows.filter((r) => r.id !== row.id))}
                    >
                      <Trash2 className="size-4" />
                    </Button>
                  </IconTooltip>
                </div>
                {error && (
                  <p
                    id={errorId}
                    className="col-start-2 col-end-[-1] row-start-3 text-xs text-destructive md:row-start-2"
                  >
                    {error}
                  </p>
                )}
              </li>
            )
          })}
        </ol>
      )}
      {validation.formError && <p className="text-xs text-destructive">{validation.formError}</p>}
      <Button
        type="button"
        variant="ghost"
        disabled={!next}
        aria-describedby={next ? undefined : 'shift-add-blocked'}
        onClick={add}
        className="h-9 w-full border border-dashed text-muted-foreground hover:border-solid hover:bg-accent hover:text-accent-foreground"
      >
        <Plus className="size-4" />
        Thêm khung giờ
      </Button>
      {!next && (
        <p id="shift-add-blocked" className="text-xs text-muted-foreground">
          {addBlockedReason}
        </p>
      )}
    </div>
  )
}
