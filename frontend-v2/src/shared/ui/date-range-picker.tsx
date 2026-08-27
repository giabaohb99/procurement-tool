import { CalendarRange, X } from 'lucide-react'
import { useState } from 'react'
import type { DateRange } from 'react-day-picker'

import { Button } from '@/shared/ui/button'
import { Calendar } from '@/shared/ui/calendar'
import { DATE_RANGE_PRESETS } from '@/shared/ui/date-range-presets'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'
import { formatDate, parseLocalDate, toDateInputValue } from '@/shared/utils/format-date'

export interface DateRangePickerProps {
  /** `yyyy-mm-dd` — đúng dạng API nhận và trả. Rỗng = chưa chọn. */
  from?: string
  to?: string
  /** Gọi khi bấm **Áp dụng** hoặc **chọn nhanh**; xóa thì trả hai chuỗi rỗng. */
  onChange: (from: string, to: string) => void
  placeholder?: string
  disabled?: boolean
  /** Tắt hàng chọn nhanh (Hôm nay / 7 ngày qua / …) nếu màn đó không cần. */
  showPresets?: boolean
  className?: string
}

/**
 * Tô DẢI cho khoảng đã chọn.
 *
 * Đè luôn `selected` của `Calendar`: ở chế độ `range`, react-day-picker gắn
 * `selected` cho MỌI ngày trong khoảng, nên giữ nguyên thì cả dải thành một dãy
 * ô xanh đặc rời rạc, không thấy đâu là hai đầu. Đè bằng cách truyền lại khóa
 * `selected` (Calendar trải `...classNames` sau cùng) chứ không chồng thêm class
 * — hai chuỗi class cùng ghi `bg-*` thì thứ tự thắng thua do Tailwind sắp, không
 * đoán trước được.
 */
const RANGE_CLASS_NAMES = {
  selected: '',
  range_start: 'rounded-l-md bg-accent [&>button]:bg-primary [&>button]:text-primary-foreground',
  range_end: 'rounded-r-md bg-accent [&>button]:bg-primary [&>button]:text-primary-foreground',
  range_middle: 'bg-accent [&>button]:bg-transparent [&>button]:text-accent-foreground',
}

/** `Date` → `yyyy-mm-dd` theo giờ địa phương. */
function toValue(day: Date | undefined): string {
  return day ? toDateInputValue(day) : ''
}

function toRange(from?: string, to?: string): DateRange | undefined {
  const start = parseLocalDate(from)
  if (!start) return undefined
  return { from: start, to: parseLocalDate(to) }
}

/**
 * Chọn KHOẢNG NGÀY: lịch hai tháng + hàng chọn nhanh, chốt bằng nút **Áp dụng**.
 *
 * ⚠️ Vì sao phải có bản nháp và nút Áp dụng — đây là lỗi đã phải vá (26/08/2026,
 * khách báo "range date khó xài"): bản đầu bắn `onChange` ngay trong `onSelect`
 * rồi đóng popover. Mà react-day-picker từ v9 trả `{from: X, to: X}` ngay ở cú
 * bấm ĐẦU TIÊN, nên chốt chặn `if (!from || !to) return` lọt tuột — bấm một
 * ngày là popover đóng và áp luôn khoảng một ngày `10/08 – 10/08`. Không tài
 * nào chọn nổi một khoảng thật.
 *
 * Nay khoảng đang chọn nằm ở state NHÁP trong popover, chỉ ra ngoài khi người
 * dùng tự chốt. Nhờ vậy còn được thêm: sửa lại đầu đã chọn hụt mà bảng bên dưới
 * không nháy số theo từng cú bấm, và bấm ra ngoài = hủy chứ không phải lỡ tay
 * đổi bộ lọc.
 *
 * Chọn nhanh thì áp NGAY và đóng — một cú bấm là xong, bắt bấm thêm "Áp dụng"
 * nữa thì gọi gì là chọn nhanh.
 */
export function DateRangePicker({
  from,
  to,
  onChange,
  placeholder = 'Chọn khoảng ngày',
  disabled,
  showPresets = true,
  className,
}: DateRangePickerProps) {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState<DateRange | undefined>(undefined)
  /** Cú bấm tới là chọn ngày KẾT THÚC (đã có ngày bắt đầu)? */
  const [pickingEnd, setPickingEnd] = useState(false)

  const hasValue = Boolean(from && to)
  const canApply = Boolean(draft?.from && draft?.to)

  function handleOpenChange(next: boolean) {
    //  Nạp lại bản nháp mỗi lần MỞ, không phải mỗi lần đóng: đóng bằng cách bấm
    //  ra ngoài nghĩa là hủy, lần mở sau phải thấy đúng khoảng đang áp dụng.
    if (next) {
      setDraft(toRange(from, to))
      setPickingEnd(false)
    }
    setOpen(next)
  }

  /**
   * Hai nhịp chọn do CHÍNH component đếm, không hỏi react-day-picker.
   *
   * Vì `mode="range"` của react-day-picker trả `{from: X, to: X}` ngay cú bấm
   * ĐẦU TIÊN, nên không thể nhìn vào "nháp đã đủ hai đầu chưa" mà đoán người
   * dùng đang ở nhịp nào — đủ ngay từ cú thứ nhất. Nó cũng NONG khoảng cũ ra
   * thay vì chọn lại: đang có 10/08–20/08 mà bấm 28/08 thì ra 10/08–28/08, muốn
   * khoảng mới phải bấm ✕ xóa trước. Cả hai đúng chỗ khách kêu "khó xài".
   *
   * Nhịp 1 = ngày bắt đầu (xóa đầu kia đi), nhịp 2 = ngày kết thúc. Bấm ngược
   * (kết thúc trước bắt đầu) thì tự đảo lại, đừng gửi `from > to` lên backend —
   * danh sách trả về rỗng và người dùng tưởng không có dữ liệu.
   */
  function pickDay(clicked: Date | undefined) {
    if (!clicked) return
    if (!pickingEnd || !draft?.from) {
      setDraft({ from: clicked, to: undefined })
      setPickingEnd(true)
      return
    }
    const isReversed = clicked.getTime() < draft.from.getTime()
    setDraft(isReversed ? { from: clicked, to: draft.from } : { from: draft.from, to: clicked })
    setPickingEnd(false)
  }

  function apply(nextFrom: string, nextTo: string) {
    onChange(nextFrom, nextTo)
    setOpen(false)
  }

  return (
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          disabled={disabled}
          className={cn(
            'w-auto min-w-56 justify-start gap-2 font-normal',
            !hasValue && 'text-muted-foreground',
            className,
          )}
        >
          <CalendarRange className="size-4 shrink-0 text-muted-foreground" />
          <span className="truncate">
            {hasValue ? `${formatDate(from)} – ${formatDate(to)}` : placeholder}
          </span>
          {hasValue && (
            <span
              role="button"
              tabIndex={-1}
              aria-label="Xóa khoảng ngày"
              className="transition-colors ml-auto shrink-0 rounded-full p-0.5 text-muted-foreground hover:bg-muted hover:text-foreground"
              //  Chặn ở CẢ HAI nhịp. `Popover` của Radix mở bằng `click`, còn
              //  `DropdownMenu` (và vài trigger khác trong hệ) mở bằng
              //  `pointerdown` — chặn thiếu nhịp nào là xóa xong lịch vẫn bung
              //  ra ngay sau lưng.
              onPointerDown={(event) => {
                event.preventDefault()
                event.stopPropagation()
              }}
              onClick={(event) => {
                event.preventDefault()
                event.stopPropagation()
                onChange('', '')
              }}
            >
              <X className="size-3.5" />
            </span>
          )}
        </Button>
      </PopoverTrigger>

      <PopoverContent className="w-auto p-0" align="start">
        {showPresets && (
          <div className="flex flex-wrap gap-1.5 border-b p-3">
            {DATE_RANGE_PRESETS.map((preset) => (
              <Button
                key={preset.label}
                type="button"
                variant="secondary"
                size="xs"
                onClick={() => apply(...preset.resolve())}
              >
                {preset.label}
              </Button>
            ))}
          </div>
        )}

        <Calendar
          mode="range"
          numberOfMonths={2}
          //  Mở đúng tháng của đầu khoảng đang chọn, không thì tháng nào cũng
          //  phải bấm mũi tên lùi về mới thấy khoảng cũ.
          defaultMonth={draft?.from}
          selected={draft}
          //  Chỉ lấy NGÀY VỪA BẤM, bỏ qua khoảng react-day-picker tự dựng —
          //  `pickDay` mới là chỗ quyết định (xem chú thích ở đó).
          onSelect={(_range, clicked) => pickDay(clicked)}
          classNames={RANGE_CLASS_NAMES}
        />

        <div className="flex items-center justify-between gap-3 border-t p-3">
          <p className="text-sm text-muted-foreground">
            {draft?.from ? (
              <>
                <span className="font-medium text-foreground">
                  {formatDate(draft.from)}
                </span>
                {' – '}
                {draft.to ? (
                  <span className="font-medium text-foreground">{formatDate(draft.to)}</span>
                ) : (
                  //  Nói rõ còn thiếu đầu nào, đừng để một dấu "…" câm: người
                  //  dùng bấm một cái rồi ngồi đợi không biết vì sao chưa xong.
                  <span>chọn tiếp ngày kết thúc</span>
                )}
              </>
            ) : (
              'Bấm ngày bắt đầu, rồi ngày kết thúc'
            )}
          </p>

          <div className="flex shrink-0 items-center gap-2">
            {(hasValue || draft?.from) && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => {
                  setDraft(undefined)
                  setPickingEnd(false)
                  apply('', '')
                }}
              >
                Xóa
              </Button>
            )}
            <Button
              type="button"
              size="sm"
              disabled={!canApply}
              onClick={() => {
                if (!canApply) return
                apply(toValue(draft?.from), toValue(draft?.to))
              }}
            >
              Áp dụng
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}
