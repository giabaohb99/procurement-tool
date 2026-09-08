import { ChevronLeft, ChevronRight } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { rangeLabel, startOfMonth, type CalendarMode } from '../utils/calendar-grid'

interface LeaveCalendarToolbarProps {
  anchor: Date
  mode: CalendarMode
  onModeChange: (mode: CalendarMode) => void
  onShift: (step: number) => void
  onJump: (date: Date) => void
}

const MODES: { value: CalendarMode; label: string }[] = [
  { value: 'day', label: 'Ngày' },
  { value: 'week', label: 'Tuần' },
  { value: 'month', label: 'Tháng' },
]

/** Bao nhiêu năm bày ra ô chọn, tính từ năm sau lùi về. */
const YEAR_SPAN = 3

const MONTHS = Array.from({ length: 12 }, (_, i) => i)

/**
 * Thanh điều hướng của LỊCH NGHỈ.
 *
 * ⚠️ Gộp thành **ba cụm liền khối**, không rải sáu thứ rời nhau thành một hàng.
 * Bản đầu (03/09/2026) đặt tabs, hai nút mũi tên, nhãn khoảng, nút «Hôm nay» và
 * hai ô chọn cạnh nhau với cùng một khoảng hở — mắt không nhóm được cái nào với
 * cái nào, và cả dải đọc ra như sáu điều khiển không liên quan. Nay: *đi tới
 * lui* là một khối, *nhảy tháng/năm* là một khối, *đổi chế độ* là một khối.
 *
 * ⚠️ Ô chọn **Tháng và Năm hiện ở cả ba chế độ**, không riêng chế độ tháng. Nút
 * mũi tên ở chế độ ngày dịch từng ngày một — muốn xem một ngày của bốn tháng sau
 * thì phải bấm hơn trăm lần.
 */
export function LeaveCalendarToolbar({
  anchor,
  mode,
  onModeChange,
  onShift,
  onJump,
}: LeaveCalendarToolbarProps) {
  const currentYear = new Date().getFullYear()
  const years = Array.from({ length: YEAR_SPAN + 2 }, (_, i) => currentYear + 1 - i)

  //  Nhảy tới tháng/năm thì về NGÀY 1 của tháng đó. Giữ nguyên ngày trong tháng
  //  sẽ tràn khi tháng đích ngắn hơn (31/01 sang tháng 2), xem `shiftAnchor`.
  const jumpTo = (year: number, month: number) => {
    const d = startOfMonth(anchor)
    d.setFullYear(year, month, 1)
    onJump(d)
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/*  Cụm ĐI TỚI LUI — ba nút dính liền trong một khung, nút giữa là chỗ về
           hiện tại. Ghép liền để đọc ra là một bộ điều khiển, không phải ba nút
           tình cờ đứng cạnh nhau. */}
      <div className="flex items-center rounded-md border">
        <Button
          variant="ghost"
          size="icon-sm"
          className="rounded-r-none"
          aria-label="Lùi lại"
          onClick={() => onShift(-1)}
        >
          <ChevronLeft className="size-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="rounded-none border-x px-3"
          onClick={() => onJump(new Date())}
        >
          Hôm nay
        </Button>
        <Button
          variant="ghost"
          size="icon-sm"
          className="rounded-l-none"
          aria-label="Tiến tới"
          onClick={() => onShift(1)}
        >
          <ChevronRight className="size-4" />
        </Button>
      </div>

      {/*  Nhãn khoảng đang xem — cỡ chữ lớn hơn phần còn lại vì nó là câu trả
           lời cho "tôi đang nhìn lúc nào", còn mấy nút kia chỉ là cách đổi nó. */}
      <span className="text-base font-semibold tabular-nums">{rangeLabel(anchor, mode)}</span>

      {/*  Đẩy hai cụm còn lại sang phải: bên trái là "đang ở đâu", bên phải là
           "muốn nhìn thế nào" — hai việc khác nhau, tách xa cho khỏi lẫn. */}
      <div className="ml-auto flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-1.5">
          <Select
            value={String(anchor.getMonth())}
            onValueChange={(v) => jumpTo(anchor.getFullYear(), Number(v))}
          >
            <SelectTrigger size="sm" className="w-28" aria-label="Chọn tháng">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {MONTHS.map((m) => (
                <SelectItem key={m} value={String(m)}>
                  Tháng {m + 1}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={String(anchor.getFullYear())}
            onValueChange={(v) => jumpTo(Number(v), anchor.getMonth())}
          >
            <SelectTrigger size="sm" className="w-24" aria-label="Chọn năm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {years.map((y) => (
                <SelectItem key={y} value={String(y)}>
                  {y}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/*  Nhóm chế độ tự dựng thay vì `Tabs`: `TabsList` có nền `bg-muted` rất
             nhạt nên trên nền trắng nó đọc ra như ba chữ trần, không ra một bộ
             chọn. Ở đây viền rõ + ô đang chọn tô nền đặc. */}
        <div
          className="flex items-center rounded-md border p-0.5"
          role="group"
          aria-label="Chế độ xem lịch"
        >
          {MODES.map((m) => (
            <button
              key={m.value}
              type="button"
              aria-pressed={mode === m.value}
              onClick={() => onModeChange(m.value)}
              className={cn(
                'rounded-sm px-3 py-1 text-sm font-medium transition-colors',
                mode === m.value
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground',
              )}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
