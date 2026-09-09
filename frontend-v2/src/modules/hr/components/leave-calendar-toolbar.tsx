import { ChevronLeft, ChevronRight } from 'lucide-react'

import { useIsMobile } from '@/shared/hooks/use-mobile'
import { Button } from '@/shared/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import {
  buildYearOptions,
  rangeLabel,
  startOfMonth,
  type CalendarMode,
} from '../utils/calendar-grid'
import { LeaveCalendarModeSwitch } from './leave-calendar-mode-switch'
import { LeaveCalendarMonthPicker } from './leave-calendar-month-picker'

interface LeaveCalendarToolbarProps {
  anchor: Date
  mode: CalendarMode
  onModeChange: (mode: CalendarMode) => void
  onShift: (step: number) => void
  onJump: (date: Date) => void
}

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
 *
 * ⚠️ **Khổ hẹp dựng HAI HÀNG, không phải bản khổ rộng cho xuống dòng.** Để
 * `flex-wrap` tự lo thì trên máy 393px cả cụm vỡ thành **ba dòng** (đo trên bản
 * chạy) và đẩy ô lịch đầu tiên xuống quá nửa màn hình. Hai hàng ở đây là:
 *
 * · hàng 1 — `[‹] [Tháng 9/2026 ▾] [›]`: nhãn khoảng NUỐT LUÔN hai ô chọn
 *   tháng/năm, xem `LeaveCalendarMonthPicker`;
 * · hàng 2 — bộ chọn *Ngày · Tuần · Tháng* trải hết hàng, nút «Hôm nay» đứng
 *   cuối.
 *
 * ⚠️ Rẽ bằng `useIsMobile` chứ không bằng hai khối `md:hidden` / `hidden md:flex`:
 * hai khối nghĩa là **hai nút «Tháng», hai nút «Lùi lại»** cùng nằm trong cây
 * DOM: trình đọc màn hình đọc cả sáu chế độ xem, và mọi bài kiểm tìm nút theo
 * tên đều vớ phải hai kết quả.
 */
export function LeaveCalendarToolbar({
  anchor,
  mode,
  onModeChange,
  onShift,
  onJump,
}: LeaveCalendarToolbarProps) {
  const isMobile = useIsMobile()
  const years = buildYearOptions(new Date().getFullYear())
  const label = rangeLabel(anchor, mode)

  //  Nhảy tới tháng/năm thì về NGÀY 1 của tháng đó. Giữ nguyên ngày trong tháng
  //  sẽ tràn khi tháng đích ngắn hơn (31/01 sang tháng 2), xem `shiftAnchor`.
  const jumpTo = (year: number, month: number) => {
    const d = startOfMonth(anchor)
    d.setFullYear(year, month, 1)
    onJump(d)
  }

  if (isMobile) {
    return (
      <div className="flex flex-col gap-2">
        {/*  Hàng 1 — **trái là "đang ở đâu", phải là "đi đâu"**. Nhãn khoảng
             đóng vai tiêu đề (bấm vào để nhảy tháng/năm), còn hai mũi tên dính
             liền thành MỘT khối ở mép phải, cạnh nút «Hôm nay».

             ⚠️ Không cho khối nào trải hết hàng nữa. Bản trước xếp
             `[‹] [nhãn trải hết hàng] [›]`: ba khung viền rời nhau cách đều,
             mắt không nhóm được cái nào với cái nào, và khung giữa rộng gấp đôi
             chữ bên trong nên đọc ra như một ô nhập bỏ trống. */}
        <div className="flex items-center gap-1">
          <LeaveCalendarMonthPicker
            anchor={anchor}
            label={label}
            onJump={onJump}
            className="flex-1"
          />

          <Button
            variant="ghost"
            className="h-9 shrink-0 px-2.5 text-sm"
            onClick={() => onJump(new Date())}
          >
            Hôm nay
          </Button>

          <div className="flex shrink-0 items-center rounded-md border">
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
              size="icon-sm"
              className="rounded-l-none border-l"
              aria-label="Tiến tới"
              onClick={() => onShift(1)}
            >
              <ChevronRight className="size-4" />
            </Button>
          </div>
        </div>

        {/*  Hàng 2 — chỉ còn bộ chọn chế độ, kiểu CẤP HAI (chữ + gạch chân):
             dải tab chuyển màn ngay phía trên đã là nút xanh nền đặc, thêm một
             dải nền đặc nữa là hai cấp đọc thành một. Xem `LeaveCalendarModeSwitch`. */}
        <LeaveCalendarModeSwitch mode={mode} onModeChange={onModeChange} variant="underline" />
      </div>
    )
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
      <span className="text-base font-semibold tabular-nums">{label}</span>

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

        <LeaveCalendarModeSwitch mode={mode} onModeChange={onModeChange} />
      </div>
    </div>
  )
}
