import { CalendarClock, ChevronDown, X } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Calendar } from '@/shared/ui/calendar'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'
import { formatDate, parseLocalDate, toDateInputValue } from '@/shared/utils/format-date'
import { addDays, dueTone, dueToneClass, formatDueLabel } from '../utils/due-date'
import { TaskDetailRow } from './task-detail-row'

interface TaskDateRowProps {
  startDate: string
  dueDate: string
  /** Việc đã xong thì hạn thôi tô đỏ — trễ nhưng đã làm xong thì không giục nữa. */
  done: boolean
  canEdit: boolean
  onChange: (values: { start_date?: string; due_date?: string }) => void
}

/** Ô trong popover đang nhận ngày bấm trên lịch. */
type MocThoiGian = 'start' | 'due'

/**
 * Hàng THỜI GIAN, hai hình dạng:
 *
 * - **Chưa có ngày** → ba nút «Hôm nay · Ngày mai · Khác» như Lark. Hai nút đầu
 *   đặt hạn bằng một cú bấm (hai hạn hay đặt nhất), «Khác» mở lịch.
 * - **Đã có ngày** → thu về MỘT giá trị kèm mũi tên (bấm để mở lại lịch) và nút
 *   ✕ xóa, đúng dáng hàng _Cột_ / _Độ ưu tiên_ ngay dưới. Giữ ba nút khi đã
 *   chọn xong thì hàng vừa dài vừa mơ hồ: không nút nào nói ra ngày đang giữ.
 *
 * Trong popover, bấm vào ô _Ngày bắt đầu_ hay _Hạn chót_ để chọn lịch đang sửa
 * mốc nào — một cái lịch phục vụ cả hai, khỏi lồng popover trong popover.
 */
export function TaskDateRow({ startDate, dueDate, done, canEdit, onChange }: TaskDateRowProps) {
  const [open, setOpen] = useState(false)
  const [moc, setMoc] = useState<MocThoiGian>('due')

  const homNay = addDays(0)
  const ngayMai = addDays(1)
  const coNgay = Boolean(startDate || dueDate)
  const dangSua = moc === 'due' ? dueDate : startDate

  function chon(date: Date | undefined) {
    const value = date ? toDateInputValue(date) : ''
    onChange(moc === 'due' ? { due_date: value } : { start_date: value })
  }

  return (
    <TaskDetailRow icon={CalendarClock} srLabel="Thời gian">
      <Popover open={open} onOpenChange={setOpen}>
        {coNgay ? (
          <span className="flex items-center gap-0.5">
            <PopoverTrigger asChild>
              <button
                type="button"
                disabled={!canEdit}
                aria-label="Đổi thời gian"
                className={cn(
                  'flex items-center gap-1.5 rounded-md px-1.5 py-1 text-sm',
                  //  Hạn quá / đến hôm nay thì chính giá trị đổi màu, khỏi thêm
                  //  chip cảnh báo — đúng cách thẻ kanban đang tô.
                  dueDate && dueToneClass(dueTone(dueDate, done)),
                  canEdit ? 'hover:bg-accent' : 'cursor-default',
                )}
              >
                {moTaKhoang(startDate, dueDate)}
                {canEdit && <ChevronDown className="size-4 opacity-50" />}
              </button>
            </PopoverTrigger>
            {canEdit && (
              <IconTooltip label="Xóa thời gian">
                <button
                  type="button"
                  aria-label="Xóa thời gian"
                  onClick={() => onChange({ start_date: '', due_date: '' })}
                  className="rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
                >
                  <X className="size-3.5" />
                </button>
              </IconTooltip>
            )}
          </span>
        ) : (
          <>
            <DateChip disabled={!canEdit} onClick={() => onChange({ due_date: homNay })}>
              Hôm nay
            </DateChip>
            <DateChip disabled={!canEdit} onClick={() => onChange({ due_date: ngayMai })}>
              Ngày mai
            </DateChip>
            <PopoverTrigger asChild>
              <DateChip disabled={!canEdit}>Khác</DateChip>
            </PopoverTrigger>
          </>
        )}

        <PopoverContent align="start" className="w-auto p-0">
          <Calendar
            mode="single"
            autoFocus
            selected={parseLocalDate(dangSua)}
            defaultMonth={parseLocalDate(dangSua)}
            onSelect={chon}
          />

          <div className="space-y-1.5 border-t p-3">
            <DateSlot
              label="Ngày bắt đầu (tùy chọn)"
              value={startDate}
              focused={moc === 'start'}
              onFocus={() => setMoc('start')}
              onClear={() => onChange({ start_date: '' })}
            />
            <DateSlot
              label="Hạn chót"
              value={dueDate}
              focused={moc === 'due'}
              onFocus={() => setMoc('due')}
              onClear={() => onChange({ due_date: '' })}
            />
          </div>

          <div className="flex justify-end border-t p-2">
            <Button
              variant="ghost"
              size="sm"
              className="text-muted-foreground"
              onClick={() => onChange({ start_date: '', due_date: '' })}
            >
              Xóa cả hai ngày
            </Button>
          </div>
        </PopoverContent>
      </Popover>
    </TaskDetailRow>
  )
}

/**
 * Chữ của hàng khi đã có ngày. Có cả hai mốc thì rút gọn còn ngày/tháng —
 * `29/08/2026 → 01/09/2026` dài gấp đôi mà năm thì thường thừa.
 */
function moTaKhoang(startDate: string, dueDate: string): string {
  if (startDate && dueDate) return `${formatDueLabel(startDate)} → ${formatDueLabel(dueDate)}`
  if (dueDate) return formatDate(dueDate)
  return `từ ${formatDate(startDate)}`
}

function DateChip({
  disabled,
  className,
  onClick,
  children,
  ...props
}: React.ComponentProps<'button'>) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={cn(
        'rounded-md bg-accent px-2 py-1 text-xs text-muted-foreground transition-colors',
        disabled ? 'cursor-default' : 'hover:text-foreground',
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}

/**
 * Một ô ngày trong popover. Nhìn như ô nhập nhưng KHÔNG cho gõ: giá trị chỉ đến
 * từ lịch ngay bên trên, bấm vào đây là chọn xem lịch đang sửa mốc nào.
 */
function DateSlot({
  label,
  value,
  focused,
  onFocus,
  onClear,
}: {
  label: string
  value: string
  focused: boolean
  onFocus: () => void
  onClear: () => void
}) {
  return (
    <div
      className={cn(
        'flex h-9 w-64 items-center gap-2 rounded-md border px-3 text-sm',
        focused && 'border-primary ring-[3px] ring-ring/40',
      )}
    >
      <button type="button" onClick={onFocus} className="flex-1 text-left">
        {value ? formatDate(value) : <span className="text-muted-foreground">{label}</span>}
      </button>
      {value && (
        <IconTooltip label={`Xóa ${label.toLowerCase()}`}>
          <button
            type="button"
            aria-label={`Xóa ${label}`}
            onClick={onClear}
            className="text-muted-foreground hover:text-foreground"
          >
            <X className="size-3.5" />
          </button>
        </IconTooltip>
      )}
    </div>
  )
}
