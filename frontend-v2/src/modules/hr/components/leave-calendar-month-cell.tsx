import { cn } from '@/shared/utils/cn'
import type { LeaveRequest } from '../types/leave'
import { LeaveCalendarEntry } from './leave-calendar-entry'
import { monthCellDayLabel, splitMonthCellLines } from '../utils/month-cell-lines'

interface LeaveCalendarMonthCellProps {
  date: Date
  inMonth: boolean
  items: LeaveRequest[]
  holidayNames: string[]
  weekend: boolean
  today: boolean
  onPick: (date: Date) => void
  /** Mấy dòng chip lọt trong ô — đo từ chiều cao thật, xem `monthCellLinesFor`. */
  lines?: number
}

/**
 * MỘT Ô LỊCH THÁNG ở khổ đủ rộng — dựng theo lối **Google Calendar** (chốt
 * 09/09/2026, khách chỉ định).
 *
 * Ba điểm làm nên lối đó, và cả ba đều là lý do chứ không phải sở thích:
 *
 * · **Số ngày canh GIỮA ở đầu ô.** Canh trái thì con số dính vào đường kẻ dọc
 *   và bị chip bên dưới kéo mắt lệch sang trái; canh giữa cho một cột số thẳng
 *   hàng, lướt dọc cả tháng không phải dò.
 * · **Không tô nền ô.** Bản trước tô xám cuối tuần và xám nhạt cho ngày ngoài
 *   tháng — ba sắc xám cạnh nhau (nền tháng, nền cuối tuần, nền ngoài tháng)
 *   làm lưới trông lem nhem, mà chính chip màu mới là thứ cần nổi lên. Nay chỉ
 *   **làm nhạt CHỮ**; nền để trắng, trừ ngày lễ (xem dưới).
 * · **«+N người nữa» là DÒNG CUỐI, và nó CHIẾM CHỖ của một chip.** Ô cao ~95px
 *   chứa bốn dòng; ngày có 5 người mà cứ vẽ 3 chip rồi thêm dòng "+2" là năm
 *   dòng, dòng cuối bị đường kẻ ô cắt ngang — đúng lúc đông người mới cần lối
 *   xem tiếp. Vậy nên bớt một chip: 2 chip + «+3 người nữa». Phép chia dòng nằm
 *   ở `splitMonthCellLines`.
 *
 * ⚠️ **Ngày lễ vẫn tô nền hồng nhạt** — chỗ này cố ý KHÁC Google Calendar. Với
 * GCal ngày lễ chỉ là một sự kiện; với bảng công thì nó là *cả công ty nghỉ*,
 * và người xếp việc cần thấy điều đó khi lướt cả tháng chứ không phải khi đọc
 * tới dòng chữ trong ô. Tên ngày lễ bày thành **chip đầu tiên** (đúng lối GCal),
 * không còn nép ở góc phải cạnh con số.
 */
export function LeaveCalendarMonthCell({
  date,
  inMonth,
  items,
  holidayNames,
  weekend,
  today,
  onPick,
  lines,
}: LeaveCalendarMonthCellProps) {
  const { visible, hidden } = splitMonthCellLines(items.length, holidayNames.length > 0, lines)

  return (
    <div
      className={cn(
        //  `overflow-hidden` là lưới đỡ cuối: cửa sổ thấp thì bốn dòng cũng
        //  không vừa, và chip tràn ra sẽ nằm đè lên ô hàng dưới — người xem đọc
        //  thành "người này nghỉ ngày kia".
        'flex min-h-0 min-w-0 flex-col gap-0.5 overflow-hidden border-r border-b p-1 last:border-r-0',
        !inMonth && 'text-muted-foreground/60',
        holidayNames.length > 0 && 'bg-rose-50/60 dark:bg-rose-950/20',
      )}
    >
      <div className="flex shrink-0 justify-center">
        <button
          type="button"
          onClick={() => onPick(date)}
          title="Xem chi tiết ngày này"
          className={cn(
            'rounded-full px-1 text-xs tabular-nums transition-colors hover:bg-accent',
            inMonth ? 'font-medium' : 'text-muted-foreground/60',
            weekend && inMonth && 'font-normal text-muted-foreground',
            //  Hôm nay: chấm tròn đặc thay vì viền cả ô — viền quanh ô trong một
            //  lưới toàn đường kẻ thì lẫn vào chính lưới đó.
            today &&
              'grid size-6 place-items-center bg-primary px-0 font-semibold text-primary-foreground hover:bg-primary/90',
          )}
        >
          {monthCellDayLabel(date, today)}
        </button>
      </div>

      {holidayNames.length > 0 && (
        <span
          className="truncate rounded bg-rose-100 px-1.5 text-[11px] leading-4 font-medium text-rose-800 dark:bg-rose-950 dark:text-rose-200"
          title={holidayNames.join(' · ')}
        >
          {holidayNames[0]}
        </span>
      )}

      {items.slice(0, visible).map((r) => (
        <LeaveCalendarEntry key={r.id} request={r} />
      ))}

      {hidden > 0 && (
        <button
          type="button"
          onClick={() => onPick(date)}
          className="rounded-sm px-1 text-left text-[11px] font-medium text-muted-foreground hover:underline"
        >
          +{hidden} người nữa
        </button>
      )}
    </div>
  )
}
