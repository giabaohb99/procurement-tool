import { cn } from '@/shared/utils/cn'
import type { CalendarMode } from '../utils/calendar-grid'

interface LeaveCalendarModeSwitchProps {
  mode: CalendarMode
  onModeChange: (mode: CalendarMode) => void
  /**
   * `segmented` = ba ô trong một khung viền, ô đang chọn tô nền đặc (khổ rộng).
   * `underline` = chữ trần + gạch chân (khổ điện thoại) — xem docstring.
   */
  variant?: 'segmented' | 'underline'
}

const MODES: { value: CalendarMode; label: string }[] = [
  { value: 'day', label: 'Ngày' },
  { value: 'week', label: 'Tuần' },
  { value: 'month', label: 'Tháng' },
]

/**
 * Bộ chọn NGÀY · TUẦN · THÁNG của Lịch nghỉ.
 *
 * ⚠️ Bản `segmented` tự dựng thay vì dùng `Tabs`: `TabsList` có nền `bg-muted`
 * rất nhạt nên trên nền trắng nó đọc ra như ba chữ trần, không ra một bộ chọn.
 * Ở đây viền rõ + ô đang chọn tô nền đặc.
 *
 * ⚠️ **Khổ điện thoại phải là bản `underline`, và đây là chuyện THỨ BẬC chứ
 * không phải thẩm mỹ.** Ngay phía trên bộ chọn này là dải tab chuyển màn (*Đơn
 * nghỉ phép · Lịch nghỉ · Quỹ phép năm · Thiết lập*) — nút xanh nền đặc. Bản
 * `segmented` trải hết hàng thì dải dưới **to hơn và xanh hơn dải trên**, hai
 * dải đọc thành cùng một cấp và mắt không biết cái nào chuyển màn, cái nào đổi
 * cách nhìn (khách bác 09/09/2026: *"tab này làm lại theo hướng khác ở mobile"*).
 * Chữ + gạch chân là đúng kiểu tab con đã dùng ở «Thiết lập ▸ Loại nghỉ / Lịch
 * ngày lễ» (`LeaveSectionTabs.SubTabLink`) — cùng một hệ, không phải phát minh
 * thêm kiểu thứ ba.
 */
export function LeaveCalendarModeSwitch({
  mode,
  onModeChange,
  variant = 'segmented',
}: LeaveCalendarModeSwitchProps) {
  if (variant === 'underline') {
    return (
      <div className="flex items-center gap-5" role="group" aria-label="Chế độ xem lịch">
        {MODES.map((m) => (
          <button
            key={m.value}
            type="button"
            aria-pressed={mode === m.value}
            onClick={() => onModeChange(m.value)}
            //  `px-1` + `pt-1 pb-1.5` cho vùng chạm ~34px mà vẫn là chữ trần:
            //  nhãn chỉ rộng 40px nên không đệm thì ngón tay trượt sang nhãn
            //  bên cạnh.
            className={cn(
              'border-b-2 px-1 pt-1 pb-1.5 text-sm font-medium transition-colors',
              mode === m.value
                ? 'border-primary text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground',
            )}
          >
            {m.label}
          </button>
        ))}
      </div>
    )
  }

  return (
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
  )
}
