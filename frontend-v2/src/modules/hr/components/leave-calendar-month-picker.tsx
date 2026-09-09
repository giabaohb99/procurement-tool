import { ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'
import { buildYearOptions } from '../utils/calendar-grid'

interface LeaveCalendarMonthPickerProps {
  anchor: Date
  /** Chữ trên nút — nhãn khoảng đang xem, xem `rangeLabel`. */
  label: string
  onJump: (date: Date) => void
  className?: string
}

const MONTHS = Array.from({ length: 12 }, (_, i) => i)

/**
 * Nhảy tới THÁNG/NĂM bất kỳ ở khổ điện thoại — nhãn khoảng đang xem CHÍNH LÀ
 * nút mở bảng chọn.
 *
 * ⚠️ Đây là bản gộp của ba thứ mà khổ rộng bày rời: nhãn khoảng, ô chọn tháng,
 * ô chọn năm. Trên máy 393px, ba thứ đó cộng lại vượt một hàng nên thanh công cụ
 * tự vỡ thành ba dòng (đo trên bản chạy: **~150px** trước khi thấy ô lịch đầu
 * tiên). Mà nhãn và hai ô chọn nói **cùng một điều** — "đang xem tháng 9/2026" —
 * nên gộp lại không mất thông tin nào: chữ vẫn đó, chạm vào thì đổi được.
 *
 * ⚠️ **Không dùng `Select` trong `Popover`.** Cả hai đều portal ra ngoài cây, và
 * cú chạm vào danh sách của `Select` bị `Popover` tính là "bấm ra ngoài" nên tờ
 * chọn đóng ngay trước khi giá trị kịp đổi. Lưới 12 nút + bộ đếm năm nằm THẲNG
 * trong tờ chọn thì không có tầng portal thứ hai, mà lại còn chọn xong trong một
 * chạm thay vì ba.
 *
 * ⚠️ Dải năm lấy từ `buildYearOptions` — đúng dải mà ô chọn năm ở khổ rộng đang
 * bày. Hai bộ chọn cùng một màn mà đi tới được hai khoảng thời gian khác nhau là
 * thứ không ai báo lỗi nhưng ai gặp cũng thấy sai.
 */
export function LeaveCalendarMonthPicker({
  anchor,
  label,
  onJump,
  className,
}: LeaveCalendarMonthPickerProps) {
  const [open, setOpen] = useState(false)
  const [year, setYear] = useState(() => anchor.getFullYear())

  const years = buildYearOptions(new Date().getFullYear())
  const maxYear = years[0]
  const minYear = years[years.length - 1]

  const handleOpenChange = (next: boolean) => {
    //  Mở lại thì bắt đầu từ năm ĐANG XEM, không phải năm mình lỡ bấm tới rồi
    //  đóng tờ chọn lần trước — người dùng đọc "Tháng 9/2026" trên nút mà bảng
    //  mở ra lại đứng ở 2024 thì không hiểu mình đang chọn cho năm nào.
    if (next) setYear(anchor.getFullYear())
    setOpen(next)
  }

  const pick = (month: number) => {
    //  Về NGÀY 1 của tháng đích: giữ nguyên ngày trong tháng sẽ tràn khi tháng
    //  đích ngắn hơn (31/01 sang tháng 2), cùng bài học với `shiftAnchor`.
    onJump(new Date(year, month, 1))
    setOpen(false)
  }

  return (
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        {/*  ⚠️ Kiểu **TIÊU ĐỀ**, không phải kiểu ô nhập: nền chìm, chữ to, canh
             trái, đệm hẹp. Bản đầu (09/09/2026) dùng `variant="outline"` và cho
             trải hết hàng — khung viền rộng 250px ôm một dòng chữ 110px nằm
             giữa, nhìn ra đúng một ô nhập liệu đang bỏ trống chứ không ra nhãn
             của cái lịch. `-ml-2` để mép chữ thẳng hàng với nội dung trang, bù
             lại phần đệm của nút. */}
        <Button
          variant="ghost"
          className={cn('-ml-2 h-9 min-w-0 justify-start gap-1 px-2', className)}
        >
          <span className="truncate text-base font-semibold tabular-nums">{label}</span>
          <ChevronDown className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
        </Button>
      </PopoverTrigger>

      <PopoverContent align="start" className="w-64 p-3">
        <div className="mb-2 flex items-center justify-between">
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Năm trước"
            disabled={year <= minYear}
            onClick={() => setYear((y) => y - 1)}
          >
            <ChevronLeft className="size-4" />
          </Button>
          <span className="text-sm font-semibold tabular-nums">{year}</span>
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Năm sau"
            disabled={year >= maxYear}
            onClick={() => setYear((y) => y + 1)}
          >
            <ChevronRight className="size-4" />
          </Button>
        </div>

        <div className="grid grid-cols-3 gap-1.5">
          {MONTHS.map((m) => {
            const current = m === anchor.getMonth() && year === anchor.getFullYear()
            return (
              <button
                key={m}
                type="button"
                //  `aria-current` chứ không chỉ tô màu: tháng đang xem phải nói
                //  được thành lời cho trình đọc màn hình, không thì cả lưới là
                //  mười hai nút giống hệt nhau.
                aria-current={current ? 'true' : undefined}
                onClick={() => pick(m)}
                className={cn(
                  'rounded-md py-2 text-sm font-medium transition-colors',
                  current
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-accent hover:text-foreground',
                )}
              >
                Tháng {m + 1}
              </button>
            )
          })}
        </div>
      </PopoverContent>
    </Popover>
  )
}
