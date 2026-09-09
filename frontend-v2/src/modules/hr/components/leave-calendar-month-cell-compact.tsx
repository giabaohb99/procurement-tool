import { cn } from '@/shared/utils/cn'
import { LEAVE_STATUS, type LeaveRequest } from '../types/leave'
import { monthCellDayLabel } from '../utils/month-cell-lines'

interface LeaveCalendarMonthCellCompactProps {
  date: Date
  inMonth: boolean
  items: LeaveRequest[]
  holidayNames: string[]
  weekend: boolean
  today: boolean
  onPick: (date: Date) => void
}

/**
 * Quá số vạch này thì chồng vạch cao hơn ô 64px — phần dư gộp thành «+N».
 *
 * Tính: con số ngày 20px + 3 vạch (3×6 + 2×2 khe = 22px) + dòng «+N» 12px +
 * đệm 8px = 62px, vừa sát trần 64px của ô. Dày hơn 6px hoặc thêm vạch thứ tư là
 * tràn — lúc đó phải nới `min-h` của ô lên trước.
 */
const MAX_BARS = 3

/**
 * MỘT Ô LỊCH THÁNG ở khổ hẹp — **số ngày canh giữa, dưới là hàng chấm**, đúng
 * lối Google Calendar trên điện thoại (chốt 09/09/2026, khách chỉ định).
 *
 * ⚠️ Vì sao không kê tên: trên máy 393px một ô của lưới 7 cột rộng **~48px**.
 * Chip tên của khổ rộng đặt vào đó cắt còn ba ký tự — màn hình bày ra «Deg»,
 * «Phạ», «Hồ», ba mẩu chữ không nói được ai nghỉ mà vẫn ăn trọn chiều cao ô và
 * tràn sang hàng dưới (ảnh báo lỗi 09/09/2026: ô ngày 21 đè lên ô ngày 14).
 *
 * ⚠️ **Một VẠCH NGANG = một người** — không phải chấm, không phải huy hiệu đếm.
 * Cả ba bản đều đã dựng, đây là bản thứ ba và lý do bỏ hai bản kia:
 *
 * · *huy hiệu đếm* («●3 ●1»): hai viên có viền trong một ô 48px là hai khối chữ
 *   nhật cạnh nhau, nặng hơn hẳn phần lịch còn lại — mắt bị chúng kéo trước cả
 *   con số ngày;
 * · *chấm tròn* (lối Google Calendar): nhẹ, nhưng mỗi ô một số chấm khác nhau
 *   nên chúng canh giữa ở những vị trí khác nhau — cả lưới thành một đám hạt
 *   rải lởm chởm, không hàng không lối (khách bác 09/09/2026).
 *
 * Vạch thì **mọi vạch cùng bề rộng, cùng mép trái, cùng mép phải**: mắt đọc ra
 * một CHỒNG xếp thẳng chứ không phải một đám hạt, mà vẫn giữ nguyên hai điều
 * cần nhất — *bao nhiêu người* (đếm vạch) và *chắc chắn nghỉ hay mới xin nghỉ*
 * (xanh / vàng). Số đầy đủ vẫn có trong `aria-label` và ở chế độ Ngày.
 *
 * ⚠️ **Cả ô là MỘT nút**, không phải nút số ngày nằm trong ô. Ngón tay không
 * nhắm được vào con số 12px; cả ô thì 48×64px, vượt mốc 44px của vùng chạm. Kéo
 * theo: bên trong ô **không được có nút nào nữa** — nút lồng nút là HTML sai và
 * trình duyệt xử lý mỗi nơi một kiểu.
 *
 * ⚠️ **TÊN người không có ở chế độ tháng trên điện thoại — cố ý.** Đã dựng một
 * bản liệt kê dọc dưới lưới để bù, rồi bỏ (09/09/2026): một tháng 21 lượt nghỉ
 * ra 21 hàng dài hơn 2000px, và nó nói lại gần đúng thứ chế độ TUẦN đã bày sẵn.
 * Đường xem tên là **đổi sang Tuần** hoặc **chạm vào ô** để mở chế độ Ngày.
 */
export function LeaveCalendarMonthCellCompact({
  date,
  inMonth,
  items,
  holidayNames,
  weekend,
  today,
  onPick,
}: LeaveCalendarMonthCellCompactProps) {
  const approved = items.filter((r) => r.status === LEAVE_STATUS.APPROVED).length
  const pending = items.length - approved
  //  Xếp ĐÃ DUYỆT lên trên, chờ duyệt xuống dưới — đúng thứ tự của chú thích màu
  //  phía trên lịch. Để nguyên thứ tự dữ liệu thì chồng vạch ra xanh-vàng-xanh
  //  xen kẽ, mắt phải đếm từng vạch mới biết bao nhiêu người chắc chắn nghỉ.
  const ordered = [...items].sort(
    (a, b) =>
      Number(b.status === LEAVE_STATUS.APPROVED) - Number(a.status === LEAVE_STATUS.APPROVED),
  )
  //  Ngày lễ cũng chiếm một vạch (nó là "sự kiện cả ngày" của ô), nên trừ ra —
  //  không trừ thì ngày lễ có người nghỉ luôn cao hơn ô một vạch.
  const bars = ordered.slice(0, holidayNames.length > 0 ? MAX_BARS - 1 : MAX_BARS)
  const hidden = items.length - bars.length

  //  Tên ngày lễ và số người không có chỗ để hiện thành chữ (xem docstring) nên
  //  phải nói bằng lời cho trình đọc màn hình.
  const label = [
    `Ngày ${date.getDate()}/${date.getMonth() + 1}`,
    holidayNames.length > 0 ? holidayNames.join(' · ') : '',
    items.length > 0
      ? `${items.length} người nghỉ (${approved} đã duyệt, ${pending} chờ duyệt)`
      : 'không ai nghỉ',
  ]
    .filter(Boolean)
    .join(' — ')

  return (
    <button
      type="button"
      onClick={() => onPick(date)}
      aria-label={label}
      className={cn(
        //  `min-h-16` chứ không để lưới tự chia: ở khổ hẹp trang KHÔNG còn cao
        //  cố định (xem `leave-calendar-page`), nên `grid-rows-6` không có chiều
        //  cao nào để chia và mọi ô co lại bằng con số bên trong. 64px × 6 hàng
        //  ≈ 384px — lưới vẫn gọn trong một màn 852px mà vùng chạm thì rộng rãi.
        //  `items-stretch` (mặc định) chứ không `items-center`: vạch phải trải
        //  hết bề ngang ô thì cả lưới mới thẳng hàng — xem docstring.
        'flex min-h-16 min-w-0 flex-col gap-1 border-r border-b p-1 pt-1.5 last:border-r-0',
        //  Không tô nền cuối tuần / ngoài tháng, chỉ làm nhạt CHỮ — xem
        //  `LeaveCalendarMonthCell`. Ngày lễ vẫn tô, vì đó là cả công ty nghỉ.
        !inMonth && 'text-muted-foreground/60',
        holidayNames.length > 0 && 'bg-rose-50/60 dark:bg-rose-950/20',
      )}
    >
      {/*  Con số canh giữa như bản khổ rộng — cả cột số thẳng hàng thì lướt dọc
           cả tháng không phải dò. Bọc trong một hàng riêng vì ô nay `stretch`. */}
      <span className="flex justify-center">
        <span
          className={cn(
            'text-xs tabular-nums',
            inMonth ? 'font-medium' : 'text-muted-foreground/60',
            weekend && inMonth && 'font-normal text-muted-foreground',
            today &&
              'grid size-6 place-items-center rounded-full bg-primary font-semibold text-primary-foreground',
          )}
        >
          {monthCellDayLabel(date, today)}
        </span>
      </span>

      {(holidayNames.length > 0 || items.length > 0) && (
        <span aria-hidden="true" className="flex flex-col gap-0.5">
          {/*  Ngày lễ là vạch đầu tiên: nó cũng là một "sự kiện cả ngày" của ô,
               và nền hồng một mình dễ bị đọc nhầm thành nền xám cuối tuần. */}
          {holidayNames.length > 0 && <span className="h-1.5 rounded-full bg-rose-300" />}

          {bars.map((r) => (
            <span
              key={r.id}
              className={cn(
                'h-1.5 rounded-full',
                r.status === LEAVE_STATUS.APPROVED ? 'bg-emerald-500' : 'bg-amber-500',
              )}
            />
          ))}

          {hidden > 0 && (
            <span className="text-center text-[9px] leading-none font-medium text-muted-foreground tabular-nums">
              +{hidden}
            </span>
          )}
        </span>
      )}
    </button>
  )
}
