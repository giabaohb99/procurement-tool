import { useId } from 'react'

import { cn } from '@/shared/utils/cn'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { RequiredMark } from '@/shared/ui/required-mark'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { LEAVE_SESSION, LEAVE_SESSION_LABELS } from '../types/leave'

interface LeaveDateSessionFieldProps {
  label: string
  /**
   * Tên hàng cho trình đọc màn hình — đơn nhiều khoảng truyền «Khoảng ngày 2» để cụm ô đọc ra
   * «Khoảng ngày 2 – Từ ngày», không phải năm cụm «Từ ngày» giống hệt nhau. Mắt thường đã có
   * tiêu đề khung hàng nên phần này chỉ dành cho trình đọc màn hình (`sr-only`).
   */
  rowLabel?: string
  date: string
  session: number
  sessionLabel: string
  /** Có giá trị = buổi đang là «Theo giờ» → mọc thêm ô giờ ở cuối hàng. */
  time?: string
  timeLabel?: string
  /** Khóa mục «Theo giờ» — đơn từ hai khoảng ngày trở lên không khai theo giờ được. */
  hourlyDisabled?: boolean
  onDateChange: (value: string) => void
  onSessionChange: (value: number) => void
  onTimeChange?: (value: string) => void
}

/**
 * Một ô ngày + ô buổi đứng cùng hàng. Hai ô này luôn đi đôi (nghỉ nửa ngày là
 * chuyện thường), tách rời ra hai dòng thì người dùng chọn ngày xong không thấy
 * ô buổi ở đâu.
 *
 * Ngày dùng `DatePicker`, **không** `<input type="date">` — xem `docs/ui/date.md`:
 * ô ngày của trình duyệt mỗi hệ điều hành vẽ một kiểu, trên Windows còn hiện
 * `mm/dd/yyyy` trong khi cả hệ đọc `dd/mm/yyyy`.
 *
 * Tách khỏi `leave-request-form.tsx` (duoc-CR-683) vì mỗi khoảng ngày trên form nay là một
 * cặp ô này — `LeaveRequestPeriodsEditor` dựng nó cho từng hàng.
 */
export function LeaveDateSessionField({
  label,
  rowLabel,
  date,
  session,
  sessionLabel,
  time,
  timeLabel,
  hourlyDisabled = false,
  onDateChange,
  onSessionChange,
  onTimeChange,
}: LeaveDateSessionFieldProps) {
  const withTime = time !== undefined
  const labelId = useId()
  return (
    <div className="space-y-1.5">
      <Label id={labelId}>
        {/*  Dấu cách ĐỨNG NGOÀI thẻ `sr-only`: cách tính tên truy cập cắt khoảng trắng ở cuối
             từng thẻ con, nên để trong thẻ thì đọc dính thành «Khoảng ngày 2 –Từ ngày». */}
        {rowLabel && <span className="sr-only">{`${rowLabel} –`}</span>}
        {rowLabel && ' '}
        {label}
        <RequiredMark />
      </Label>
      {/*  Ô giờ chen vào CÙNG MỘT HÀNG với ngày và buổi: ba thứ đó là một câu
           trả lời («nghỉ từ lúc nào»), tách xuống dòng thì mắt phải ghép lại.
           ⚠️ Chỉ đúng từ `sm` trở lên. Ba ô cứng trên màn 390px thì hai ô sau
           chiếm 240px, ô NGÀY còn chưa tới 60px — không đọc nổi ngày nào. Dưới
           `sm` thì ô ngày trải hết hàng, buổi và giờ chia đôi hàng dưới: vẫn
           đọc thành một câu, chỉ là câu đó ngắt làm hai dòng. */}
      {/*  `role="group"` nối nhãn vào CẢ CỤM (ngày · buổi · giờ) thay vì `htmlFor` vào riêng nút
           ngày: `htmlFor` biến nhãn thành TÊN của nút, trình đọc màn hình mất luôn ngày đang
           chọn. Vào cụm thì nghe «Khoảng ngày 2 – Từ ngày, nhóm», rồi tới «27/10/2026, nút». */}
      <div
        role="group"
        aria-labelledby={labelId}
        className={cn(
          'grid gap-2',
          withTime
            ? 'grid-cols-2 [&>*:first-child]:col-span-2 sm:grid-cols-[minmax(0,1fr)_8rem_7rem] sm:[&>*:first-child]:col-span-1'
            : 'grid-cols-[minmax(0,1fr)_7.5rem] sm:grid-cols-[minmax(0,1fr)_9rem]',
        )}
      >
        {/*  Ô bắt buộc thì bỏ nút ✕: cho xóa là để người dùng tự tay tạo ra lỗi
             validate (docs/ui/date.md §1). */}
        <DatePicker value={date} onChange={onDateChange} clearable={false} />
        <Select value={String(session)} onValueChange={(v) => onSessionChange(Number(v))}>
          {/*  `SelectValue` sao chép children của mục đang chọn vào ô kích hoạt
               nếu không truyền children tường minh — với mục có phần chú thích
               thì ô hiện hai dòng cụt. Truyền thẳng nhãn (CR-258). */}
          <SelectTrigger className="w-full" aria-label={sessionLabel}>
            <SelectValue>{LEAVE_SESSION_LABELS[session]}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            {Object.values(LEAVE_SESSION).map((s) => (
              <SelectItem
                key={s}
                value={String(s)}
                disabled={hourlyDisabled && s === LEAVE_SESSION.HOURLY}
              >
                {LEAVE_SESSION_LABELS[s]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {withTime && (
          <Input
            type="time"
            aria-label={timeLabel}
            value={time}
            onChange={(e) => onTimeChange?.(e.target.value)}
          />
        )}
      </div>
    </div>
  )
}
