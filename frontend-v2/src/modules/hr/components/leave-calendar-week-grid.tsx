import { cn } from '@/shared/utils/cn'
import type { Holiday, LeaveRequest } from '../types/leave'
import {
  buildWeekDays,
  holidayNamesOn,
  isWeekend,
  toISODate,
  WEEKDAY_LABELS,
} from '../utils/calendar-grid'
import { LeaveCalendarEntry } from './leave-calendar-entry'

interface LeaveCalendarWeekGridProps {
  anchor: Date
  requestsOn: (iso: string) => LeaveRequest[]
  holidays: Holiday[]
  todayISO: string
  /** Mở chế độ NGÀY cho hàng vừa bấm — lối thoát khi hàng quá đông. */
  onPickDay: (date: Date) => void
}

/**
 * Quá số này thì hàng ngang bắt đầu nuốt cả màn hình — phần dư gộp thành nút
 * "+N người nữa". Sáu chip vừa đủ một hàng trên màn 24" mà không xuống dòng.
 */
const MAX_VISIBLE = 6

/**
 * TUẦN — mỗi ngày một HÀNG NGANG, không phải một cột dọc.
 *
 * ⚠️ Bản đầu (03/09/2026) dựng 7 cột dọc phủ hết chiều cao trang, và nó **xấu
 * đúng ở ca thường gặp nhất**: một tuần bình thường có một hai người nghỉ, nên
 * bảy cột cao cả nghìn pixel trống trơn tới 95%. Cột dọc chỉ đẹp khi ngày nào
 * cũng kín người — lịch nghỉ của một công ty vài chục người thì không bao giờ.
 *
 * Hàng ngang thì cao theo nội dung: ngày không ai nghỉ chỉ chiếm một dòng mỏng.
 * Cả tuần đọc từ trên xuống trong một tầm mắt, và câu hỏi *"tuần tới ai nghỉ"*
 * trả lời xong trong một lần liếc.
 *
 * ⚠️ Nhưng **cắt ở sáu người**. "Tự giãn theo nội dung" nghe thì hay, cho tới
 * hôm cả phòng ba mươi người nghỉ chung: hàng đó tự dâng lên nuốt hết màn hình
 * và sáu ngày còn lại bị đẩy khỏi tầm nhìn — đúng cái tuần bận nhất lại là tuần
 * không xem được. Phần dư thành nút sang chế độ NGÀY.
 */
export function LeaveCalendarWeekGrid({
  anchor,
  requestsOn,
  holidays,
  todayISO,
  onPickDay,
}: LeaveCalendarWeekGridProps) {
  const days = buildWeekDays(anchor)
  const total = days.reduce((sum, d) => sum + requestsOn(toISODate(d)).length, 0)

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-auto rounded-md border">
      {total === 0 && (
        //  Nói ra một lần cho cả tuần. Bảy dòng "không ai nghỉ" nối nhau đọc như
        //  màn hình hỏng chứ không như một tuần yên ả.
        <p className="border-b bg-muted/30 px-4 py-2 text-sm text-muted-foreground">
          Cả tuần này không ai nghỉ.
        </p>
      )}

      {days.map((day, i) => {
        const iso = toISODate(day)
        const items = requestsOn(iso)
        const names = holidayNamesOn(holidays, iso)
        const weekend = isWeekend(day)
        const today = iso === todayISO

        return (
          <div
            key={iso}
            className={cn(
              'flex gap-4 border-b px-4 py-2.5 last:border-b-0',
              weekend && 'bg-muted/50',
              names.length > 0 && 'bg-rose-50/60 dark:bg-rose-950/20',
              today && 'bg-primary/5',
            )}
          >
            {/*  Cột ngày rộng CỐ ĐỊNH: bảy nhãn phải thẳng hàng thì mắt mới lướt
                 dọc được, mà "T2 31/8" và "CN 6/9" dài khác nhau. */}
            <button
              type="button"
              onClick={() => onPickDay(day)}
              title="Xem chi tiết ngày này"
              className="flex w-28 shrink-0 items-baseline gap-2 text-left hover:underline"
            >
              <span
                className={cn(
                  'text-sm font-semibold',
                  today && 'text-primary',
                  weekend && !today && 'text-muted-foreground',
                )}
              >
                {WEEKDAY_LABELS[i]}
              </span>
              <span className="text-xs tabular-nums text-muted-foreground">
                {day.getDate()}/{day.getMonth() + 1}
              </span>
            </button>

            <div className="flex min-w-0 flex-1 flex-wrap items-center gap-1.5">
              {names.map((name) => (
                <span
                  key={name}
                  className="rounded-sm bg-rose-100 px-2 py-0.5 text-xs font-medium text-rose-800 dark:bg-rose-950 dark:text-rose-200"
                >
                  {name}
                </span>
              ))}

              {items.slice(0, MAX_VISIBLE).map((r) => (
                <LeaveCalendarEntry key={r.id} request={r} size="full" />
              ))}

              {items.length > MAX_VISIBLE && (
                <button
                  type="button"
                  onClick={() => onPickDay(day)}
                  className="rounded-sm px-1.5 py-1 text-xs font-medium text-primary hover:underline"
                >
                  +{items.length - MAX_VISIBLE} người nữa
                </button>
              )}

              {/*  Chỉ ghi "không ai nghỉ" khi cả dòng trống trơn — ngày lễ mà
                   không ai nghỉ thêm thì thẻ ngày lễ đã nói đủ. */}
              {items.length === 0 && names.length === 0 && (
                <span className="text-xs text-muted-foreground">Không ai nghỉ</span>
              )}
            </div>

            {items.length > 0 && (
              <span className="shrink-0 self-center text-xs tabular-nums text-muted-foreground">
                {items.length} người
              </span>
            )}
          </div>
        )
      })}
    </div>
  )
}
