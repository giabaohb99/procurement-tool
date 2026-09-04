import { cn } from '@/shared/utils/cn'
import type { Holiday, LeaveRequest } from '../types/leave'
import {
  buildMonthGrid,
  holidayNamesOn,
  isWeekend,
  toISODate,
  WEEKDAY_LABELS,
} from '../utils/calendar-grid'
import { LeaveCalendarEntry } from './leave-calendar-entry'

interface LeaveCalendarMonthGridProps {
  anchor: Date
  requestsOn: (iso: string) => LeaveRequest[]
  holidays: Holiday[]
  todayISO: string
  /** Mở chế độ NGÀY cho ô vừa bấm — lối thoát khi ô chật không chứa hết. */
  onPickDay: (date: Date) => void
}

/** Quá số này thì ô lịch tháng không còn chỗ — phần dư gộp thành "+N nữa". */
const MAX_VISIBLE = 3

/**
 * LƯỚI THÁNG — 7 cột × 6 hàng, phủ hết chiều cao còn lại của trang.
 *
 * ⚠️ `grid-rows-6` + `min-h-0` ở mọi tầng là bắt buộc để lưới CHIA ĐỀU chiều
 * cao thật. Thiếu `min-h-0` thì ô con có `overflow-auto` sẽ nong hàng ra theo
 * nội dung — ngày nào có năm người nghỉ là hàng đó cao gấp ba, và cả lưới méo.
 *
 * ⚠️ Mỗi ô cắt ở ba mục rồi gộp phần dư thành "+N nữa". Không cắt thì một ngày
 * cả phòng nghỉ sẽ đẩy ô cao vọt và phá lưới; cho ô cuộn riêng thì có thanh cuộn
 * tí hon trong một ô 90px, không ai kéo nổi.
 *
 * ⚠️ **"+N nữa" và số ngày phải BẤM ĐƯỢC.** Cắt bớt mà không chừa đường xem tiếp
 * thì màn hình biết có 12 người nghỉ nhưng người dùng không bao giờ đọc được tên
 * chín người còn lại — đúng lúc một ngày đông người nghỉ mới là lúc cần xem kỹ
 * nhất. Bấm vào là sang chế độ NGÀY, nơi có đủ chỗ cho tất cả.
 */
export function LeaveCalendarMonthGrid({
  anchor,
  requestsOn,
  holidays,
  todayISO,
  onPickDay,
}: LeaveCalendarMonthGridProps) {
  const cells = buildMonthGrid(anchor)

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-md border">
      {/*  Hàng tiêu đề thứ — KHÔNG nằm trong lưới 6 hàng, nếu không nó cũng bị
           chia đều chiều cao và cao bằng một ô ngày. */}
      <div className="grid shrink-0 grid-cols-7 border-b bg-muted/40">
        {WEEKDAY_LABELS.map((label, i) => (
          <div
            key={label}
            className={cn(
              'px-2 py-1.5 text-center text-xs font-medium',
              i >= 5 ? 'text-muted-foreground' : 'text-foreground',
            )}
          >
            {label}
          </div>
        ))}
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-7 grid-rows-6">
        {cells.map((cell) => {
          const iso = toISODate(cell.date)
          const items = requestsOn(iso)
          const names = holidayNamesOn(holidays, iso)
          const weekend = isWeekend(cell.date)

          return (
            <div
              key={iso}
              className={cn(
                'flex min-h-0 min-w-0 flex-col gap-0.5 border-r border-b p-1 last:border-r-0',
                //  Ngày ngoài tháng vẫn HIỆN (lưới cần lấp đầy) nhưng mờ đi —
                //  bỏ trắng thì người xem tưởng dữ liệu chưa nạp xong.
                !cell.inMonth && 'bg-muted/20 text-muted-foreground/60',
                weekend && cell.inMonth && 'bg-muted/70',
                names.length > 0 && 'bg-rose-50/60 dark:bg-rose-950/20',
              )}
            >
              <div className="flex shrink-0 items-baseline justify-between gap-1">
                <button
                  type="button"
                  onClick={() => onPickDay(cell.date)}
                  title="Xem chi tiết ngày này"
                  className={cn(
                    'rounded-full text-xs tabular-nums hover:underline',
                    cell.inMonth ? 'font-medium' : 'text-muted-foreground/60',
                    //  Hôm nay: chấm tròn đặc thay vì viền cả ô — viền quanh ô
                    //  trong một lưới toàn đường kẻ thì lẫn vào chính lưới đó.
                    iso === todayISO &&
                      'grid size-5 place-items-center bg-primary font-semibold text-primary-foreground no-underline hover:opacity-90',
                  )}
                >
                  {cell.date.getDate()}
                </button>
                {names.length > 0 && (
                  <span
                    className="truncate text-[10px] text-rose-700 dark:text-rose-300"
                    title={names.join(' · ')}
                  >
                    {names[0]}
                  </span>
                )}
              </div>

              {items.slice(0, MAX_VISIBLE).map((r) => (
                <LeaveCalendarEntry key={r.id} request={r} />
              ))}
              {items.length > MAX_VISIBLE && (
                <button
                  type="button"
                  onClick={() => onPickDay(cell.date)}
                  className="rounded-sm px-1 text-left text-[10px] font-medium text-primary hover:underline"
                >
                  +{items.length - MAX_VISIBLE} người nữa
                </button>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
