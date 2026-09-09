import { cn } from '@/shared/utils/cn'
import type { LeaveRequest } from '../types/leave'
import { LeaveCalendarEntry } from './leave-calendar-entry'

interface LeaveCalendarDayRowProps {
  date: Date
  /** Nhãn thứ («T2»…«CN») — xem `WEEKDAY_LABELS`. */
  weekdayLabel: string
  items: LeaveRequest[]
  holidayNames: string[]
  today: boolean
  weekend: boolean
  /** Mở chế độ NGÀY cho hàng này — lối thoát khi hàng quá đông. */
  onPick: (date: Date) => void
  /** Quá số này thì phần dư gộp thành nút «+N người nữa». */
  maxVisible: number
  /**
   * Ghi «Không ai nghỉ» khi hàng trống trơn. Lưới TUẦN bật (nó bày đủ bảy ngày
   * nên phải nói rõ ngày nào trống); bản liệt kê THÁNG tắt — nó chỉ liệt kê ngày
   * CÓ người, một dòng "không ai nghỉ" ở đó là tự mâu thuẫn.
   */
  showEmptyNote?: boolean
}

/**
 * MỘT NGÀY dạng HÀNG NGANG — dùng chung cho lưới tuần và bản liệt kê tháng ở
 * khổ điện thoại.
 *
 * ⚠️ Hàng ngang thay vì cột dọc, và đây là quyết định của bản tuần đầu tiên
 * (03/09/2026) nên chép lại để không ai dựng ngược: cột dọc phủ hết chiều cao
 * trang chỉ đẹp khi ngày nào cũng kín người, còn lịch nghỉ của công ty vài chục
 * người thì một tuần thường có một hai người — bảy cột cao cả nghìn pixel trống
 * tới 95%. Hàng ngang cao theo nội dung: ngày không ai nghỉ chỉ chiếm một dòng
 * mỏng, cả tuần đọc xong trong một tầm mắt.
 *
 * ⚠️ **Khổ hẹp xuống hai dòng, nhưng số đếm KHÔNG được dựng hai bản.** Bố cục
 * đổi bằng `flex-wrap` + `order`: nhãn ngày và số đếm ở dòng trên (số nép mép
 * phải), chip xuống dòng dưới nhờ `basis-full`; từ `md` thì `flex-nowrap` kéo cả
 * ba về một hàng và `md:order-3` đẩy số đếm về cuối. Dựng hai khối rồi ẩn bớt
 * bằng `md:hidden` thì con số nằm HAI LẦN trong cây DOM — trình đọc màn hình đọc
 * cả hai, và mọi bài kiểm tìm theo chữ đều vớ phải hai kết quả.
 */
export function LeaveCalendarDayRow({
  date,
  weekdayLabel,
  items,
  holidayNames,
  today,
  weekend,
  onPick,
  maxVisible,
  showEmptyNote = false,
}: LeaveCalendarDayRowProps) {
  return (
    <div
      className={cn(
        'flex flex-wrap items-center gap-x-3 gap-y-1.5 border-b px-3 py-2.5 last:border-b-0 md:flex-nowrap md:items-start md:gap-4 md:px-4',
        weekend && 'bg-muted/50',
        holidayNames.length > 0 && 'bg-rose-50/60 dark:bg-rose-950/20',
        today && 'bg-primary/5',
      )}
    >
      {/*  Cột ngày rộng CỐ ĐỊNH từ `md`: bảy nhãn phải thẳng hàng thì mắt mới
           lướt dọc được, mà "T2 31/8" và "CN 6/9" dài khác nhau. */}
      <button
        type="button"
        onClick={() => onPick(date)}
        title="Xem chi tiết ngày này"
        className="flex shrink-0 items-baseline gap-2 text-left hover:underline md:w-28"
      >
        <span
          className={cn(
            'text-sm font-semibold',
            today && 'text-primary',
            weekend && !today && 'text-muted-foreground',
          )}
        >
          {weekdayLabel}
        </span>
        <span className="text-xs tabular-nums text-muted-foreground">
          {date.getDate()}/{date.getMonth() + 1}
        </span>
      </button>

      {items.length > 0 && (
        <span className="ml-auto shrink-0 self-center text-xs tabular-nums text-muted-foreground md:order-3 md:ml-0">
          {items.length} người
        </span>
      )}

      <div className="flex min-w-0 basis-full flex-wrap items-center gap-1.5 md:order-2 md:basis-0 md:flex-1">
        {holidayNames.map((name) => (
          <span
            key={name}
            className="rounded-sm bg-rose-100 px-2 py-0.5 text-xs font-medium text-rose-800 dark:bg-rose-950 dark:text-rose-200"
          >
            {name}
          </span>
        ))}

        {items.slice(0, maxVisible).map((r) => (
          <LeaveCalendarEntry key={r.id} request={r} size="full" />
        ))}

        {items.length > maxVisible && (
          <button
            type="button"
            onClick={() => onPick(date)}
            className="rounded-sm px-1.5 py-1 text-xs font-medium text-primary hover:underline"
          >
            +{items.length - maxVisible} người nữa
          </button>
        )}

        {/*  Chỉ ghi "không ai nghỉ" khi cả dòng trống trơn — ngày lễ mà không ai
             nghỉ thêm thì thẻ ngày lễ đã nói đủ. */}
        {showEmptyNote && items.length === 0 && holidayNames.length === 0 && (
          <span className="text-xs text-muted-foreground">Không ai nghỉ</span>
        )}
      </div>
    </div>
  )
}
