import { useEffect, useRef, useState } from 'react'

import { useIsMobile } from '@/shared/hooks/use-mobile'
import type { Holiday, LeaveRequest } from '../types/leave'
import {
  buildMonthGrid,
  holidayNamesOn,
  isWeekend,
  MONTH_GRID_WEEKS,
  toISODate,
  WEEKDAY_LABELS,
} from '../utils/calendar-grid'
import { monthCellLinesFor, MONTH_CELL_CONTENT_LINES } from '../utils/month-cell-lines'
import { LeaveCalendarMonthCell } from './leave-calendar-month-cell'
import { LeaveCalendarMonthCellCompact } from './leave-calendar-month-cell-compact'

interface LeaveCalendarMonthGridProps {
  anchor: Date
  requestsOn: (iso: string) => LeaveRequest[]
  holidays: Holiday[]
  todayISO: string
  /** Mở chế độ NGÀY cho ô vừa bấm — lối thoát khi ô chật không chứa hết. */
  onPickDay: (date: Date) => void
}

/**
 * Ô hẹp hơn thế này thì chip tên không còn đọc được — đổi sang bản CHẤM
 * (`LeaveCalendarMonthCellCompact`).
 *
 * ⚠️ Đo bề rộng THẬT của lưới, không hỏi bề rộng màn hình. Cùng một máy 820px,
 * lưới rộng 530px khi menu trái mở và 740px khi thu — hỏi `useIsMobile` thì cả
 * hai đều là "khổ rộng", mà ở trường hợp đầu ô chỉ còn 75px nên tên cắt thành
 * «Dego …» y hệt lỗi trên điện thoại, chỉ khác là không ai gọi nó là điện thoại.
 *
 * Con số 92 = **đủ chỗ cho chữ đầu của tên**: 8px đệm ô + 24px viền/chấm/đệm
 * chip, còn ~60px cho chữ, tức «Nguyễn…» · «Dego Admin». Không phải mốc "tên
 * hiện đủ" — tên dài vẫn cắt ở mọi bề rộng, kể cả ô 160px của màn 24". Mốc này
 * chỉ phân biệt *cắt nhưng còn đọc ra người nào* với *cắt thành ba ký tự vô
 * nghĩa*; đặt cao hơn thì màn hình 1024px mất tên mà không cần thiết.
 */
const MIN_NAME_CELL_WIDTH = 92

/**
 * LƯỚI THÁNG — 7 cột × 6 hàng, phủ hết chiều cao còn lại của trang. Lối bày
 * theo **Google Calendar**: số ngày canh giữa, nền ô để trắng, ngày lễ và người
 * nghỉ đều là chip. Chi tiết từng ô ở `LeaveCalendarMonthCell` (khổ rộng) và
 * `LeaveCalendarMonthCellCompact` (khổ hẹp — hàng chấm thay chip).
 *
 * ⚠️ `grid-rows-6` + `min-h-0` ở mọi tầng là bắt buộc để lưới CHIA ĐỀU chiều
 * cao thật. Thiếu `min-h-0` thì ô con có `overflow-auto` sẽ nong hàng ra theo
 * nội dung — ngày nào có năm người nghỉ là hàng đó cao gấp ba, và cả lưới méo.
 *
 * ⚠️ Mỗi ô cắt bớt rồi gộp phần dư thành «+N người nữa» (`splitMonthCellLines`).
 * Không cắt thì một ngày cả phòng nghỉ sẽ đẩy ô cao vọt và phá lưới; cho ô cuộn
 * riêng thì có thanh cuộn tí hon trong một ô 90px, không ai kéo nổi.
 *
 * ⚠️ **«+N nữa» và số ngày phải BẤM ĐƯỢC.** Cắt bớt mà không chừa đường xem tiếp
 * thì màn hình biết có 12 người nghỉ nhưng người dùng không bao giờ đọc được tên
 * chín người còn lại — đúng lúc một ngày đông người nghỉ mới là lúc cần xem kỹ
 * nhất. Bấm vào là sang chế độ NGÀY, nơi có đủ chỗ cho tất cả.
 *
 * ⚠️ **Ô hẹp hơn 92px thì đổi hẳn hình dạng** — xem `MIN_NAME_CELL_WIDTH`. Ngưỡng
 * tính trên bề rộng ĐO ĐƯỢC của lưới, không trên bề rộng màn hình.
 */
export function LeaveCalendarMonthGrid({
  anchor,
  requestsOn,
  holidays,
  todayISO,
  onPickDay,
}: LeaveCalendarMonthGridProps) {
  const cells = buildMonthGrid(anchor)

  //  Hai lớp cùng trả lời một câu hỏi "ô có đủ chỗ cho cái tên không":
  //  `useIsMobile` biết ngay từ lượt vẽ ĐẦU (không có nó thì máy điện thoại
  //  loé một nhịp chip cụt chữ trước khi phép đo kịp về), còn phép đo là thứ
  //  nói đúng ở mọi bề rộng khác — nhất là khi menu trái ăn mất 256px.
  const gridRef = useRef<HTMLDivElement>(null)
  const isMobile = useIsMobile()
  const [tooNarrow, setTooNarrow] = useState(false)
  const [lines, setLines] = useState(MONTH_CELL_CONTENT_LINES)

  useEffect(() => {
    const el = gridRef.current
    if (!el) return

    const observer = new ResizeObserver((entries) => {
      const rect = entries[0]?.contentRect
      //  Bề rộng 0 nghĩa là khối đang bị ẩn (vừa đổi chế độ xem), không phải
      //  "lưới hẹp" — lấy nó làm mốc thì ô lật hình dạng ngay lúc không ai nhìn.
      if (!rect || rect.width <= 0) return
      setTooNarrow(rect.width / 7 < MIN_NAME_CELL_WIDTH)
      //  Chiều cao ô đổi theo cửa sổ, nên số chip bày được cũng đổi — xem
      //  `monthCellLinesFor`. Hai `setState` riêng, không gộp thành một object:
      //  giá trị nguyên thủy giống hệt thì React bỏ qua, khỏi vẽ lại 42 ô mỗi
      //  lần kéo cửa sổ ngang.
      setLines(monthCellLinesFor(rect.height / MONTH_GRID_WEEKS))
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  const compact = isMobile || tooNarrow

  return (
    //  ⚠️ `max-md:flex-none`: ở khổ hẹp trang bỏ chế độ `fill` nên không còn
    //  chiều cao nào để `flex-1` chiếm — giữ nó lại thì lưới co về chiều cao nội
    //  dung tối thiểu và sáu hàng dính vào nhau. Chiều cao ô khi đó do
    //  `min-h-16` của từng ô quyết định.
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-md border max-md:flex-none">
      {/*  Hàng tiêu đề thứ — KHÔNG nằm trong lưới 6 hàng, nếu không nó cũng bị
           chia đều chiều cao và cao bằng một ô ngày.

           Chữ nhỏ, mờ, không nền: đây là nhãn của lưới chứ không phải một hàng
           dữ liệu. Dải `bg-muted` của bản trước làm nó nặng ngang một hàng ngày
           thật — xem lối Google Calendar. */}
      <div className="grid shrink-0 grid-cols-7 border-b">
        {WEEKDAY_LABELS.map((label) => (
          <div
            key={label}
            className="py-1.5 text-center text-[11px] font-medium text-muted-foreground"
          >
            {label}
          </div>
        ))}
      </div>

      <div ref={gridRef} className="grid min-h-0 flex-1 grid-cols-7 grid-rows-6">
        {cells.map((cell) => {
          const iso = toISODate(cell.date)
          const cellProps = {
            date: cell.date,
            inMonth: cell.inMonth,
            items: requestsOn(iso),
            holidayNames: holidayNamesOn(holidays, iso),
            weekend: isWeekend(cell.date),
            today: iso === todayISO,
            onPick: onPickDay,
          }

          return compact ? (
            <LeaveCalendarMonthCellCompact key={iso} {...cellProps} />
          ) : (
            <LeaveCalendarMonthCell key={iso} {...cellProps} lines={lines} />
          )
        })}
      </div>
    </div>
  )
}
