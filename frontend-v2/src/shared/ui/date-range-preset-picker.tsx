import { Calendar as CalendarIcon, X } from 'lucide-react'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'

export interface DateRangePresetPickerProps {
  from?: string
  to?: string
  onChange: (from: string, to: string) => void
  placeholder?: string
  className?: string
}

function formatDate(date: Date): string {
  const yyyy = date.getFullYear()
  const mm = String(date.getMonth() + 1).padStart(2, '0')
  const dd = String(date.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

export function DateRangePresetPicker({
  from = '',
  to = '',
  onChange,
  placeholder = 'Khoảng ngày...',
  className,
}: DateRangePresetPickerProps) {
  const hasValue = Boolean(from || to)

  const setToday = () => {
    const today = formatDate(new Date())
    onChange(today, today)
  }

  const setThisWeek = () => {
    const now = new Date()
    const day = now.getDay()
    const diffToMonday = now.getDate() - day + (day === 0 ? -6 : 1)
    const monday = new Date(now.setDate(diffToMonday))
    const sunday = new Date(monday)
    sunday.setDate(monday.getDate() + 6)
    onChange(formatDate(monday), formatDate(sunday))
  }

  const setThisMonth = () => {
    const now = new Date()
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0)
    onChange(formatDate(firstDay), formatDate(lastDay))
  }

  const setThisQuarter = () => {
    const now = new Date()
    const qMonth = Math.floor(now.getMonth() / 3) * 3
    const firstDay = new Date(now.getFullYear(), qMonth, 1)
    const lastDay = new Date(now.getFullYear(), qMonth + 3, 0)
    onChange(formatDate(firstDay), formatDate(lastDay))
  }

  const clear = () => {
    onChange('', '')
  }

  const displayLabel = hasValue
    ? `${from ? from : '...'} -> ${to ? to : '...'}`
    : placeholder

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={cn(
            'h-9 justify-start text-left font-normal text-xs px-2.5',
            !hasValue && 'text-muted-foreground',
            className,
          )}
        >
          <CalendarIcon className="mr-1.5 h-3.5 w-3.5" />
          <span className="truncate">{displayLabel}</span>
          {hasValue && (
            <span
              role="button"
              className="ml-auto rounded-full p-0.5 hover:bg-muted"
              onClick={(e) => {
                e.stopPropagation()
                clear()
              }}
            >
              <X className="h-3 w-3" />
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-3" align="start">
        <div className="space-y-3">
          <div className="text-xs font-semibold text-muted-foreground">Chọn nhanh:</div>
          <div className="grid grid-cols-2 gap-1.5">
            <Button variant="secondary" size="sm" className="h-7 text-xs" onClick={setToday}>
              Hôm nay
            </Button>
            <Button variant="secondary" size="sm" className="h-7 text-xs" onClick={setThisWeek}>
              Tuần này
            </Button>
            <Button variant="secondary" size="sm" className="h-7 text-xs" onClick={setThisMonth}>
              Tháng này
            </Button>
            <Button variant="secondary" size="sm" className="h-7 text-xs" onClick={setThisQuarter}>
              Quý này
            </Button>
          </div>

          <div className="border-t pt-2 space-y-2">
            <div className="text-xs font-semibold text-muted-foreground">Tùy chọn mốc ngày:</div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-[11px] text-muted-foreground block mb-1">Từ ngày</label>
                <Input
                  type="date"
                  value={from}
                  className="h-8 text-xs"
                  onChange={(e) => onChange(e.target.value, to)}
                />
              </div>
              <div>
                <label className="text-[11px] text-muted-foreground block mb-1">Đến ngày</label>
                <Input
                  type="date"
                  value={to}
                  className="h-8 text-xs"
                  onChange={(e) => onChange(from, e.target.value)}
                />
              </div>
            </div>
          </div>

          {hasValue && (
            <Button variant="ghost" size="sm" className="w-full h-7 text-xs text-muted-foreground" onClick={clear}>
              Xóa khoảng ngày
            </Button>
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}
