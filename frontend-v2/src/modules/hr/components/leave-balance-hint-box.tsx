import { AlertTriangle, Info } from 'lucide-react'

import { cn } from '@/shared/utils/cn'
import { useLeaveBalanceHint } from '../hooks/use-leave'

interface LeaveBalanceHintBoxProps {
  leaveTypeId: number
  year: number
  employeeId?: number
  /** Số ngày đơn đang xin — để cảnh báo TRƯỚC khi bấm gửi duyệt. */
  requestedDays: number
}

/**
 * SỐ PHÉP CÒN LẠI — ràng buộc §6.1 của kế hoạch, lý do tồn tại của cả đợt.
 *
 * Doc gọi đây là *"chi tiết nhỏ, nhưng nó cắt phần lớn số đơn sai và phần lớn
 * câu hỏi gửi về phòng Nhân sự"*. Nó phải hiện **lúc đang nhập**, không phải
 * lúc bấm gửi duyệt rồi ăn một câu chặn.
 *
 * Ba trạng thái, mỗi cái nói một chuyện khác nhau:
 *  · loại nghỉ KHÔNG trừ quỹ → nói thẳng là không giới hạn, đừng để trống;
 *  · đủ phép                 → hiện số còn lại;
 *  · KHÔNG đủ                → cảnh báo đỏ + chỉ đường sang «Nghỉ không lương»,
 *    đúng câu backend sẽ chặn (QĐ-NP2 — không cho ứng phép).
 */
export function LeaveBalanceHintBox({
  leaveTypeId,
  year,
  employeeId = 0,
  requestedDays,
}: LeaveBalanceHintBoxProps) {
  const { data, isLoading } = useLeaveBalanceHint(leaveTypeId, year, employeeId)

  if (!leaveTypeId) {
    return (
      <div className="flex items-center rounded-md border border-dashed px-3 text-sm text-muted-foreground">
        Chọn loại nghỉ để xem số ngày phép còn lại.
      </div>
    )
  }

  if (isLoading || !data) {
    return (
      <div className="flex items-center rounded-md border border-dashed px-3 text-sm text-muted-foreground">
        Đang tra quỹ phép…
      </div>
    )
  }

  if (!data.counts_balance) {
    return (
      <div className="flex items-center gap-2 rounded-md border bg-muted/30 px-3 py-2 text-sm text-muted-foreground">
        <Info className="size-4 shrink-0" />
        Loại nghỉ này không trừ vào quỹ phép năm — không giới hạn số ngày.
      </div>
    )
  }

  const enough = requestedDays <= data.remaining_days
  //  Số còn lại SAU khi trừ chính dòng đang nhập. Làm tròn 2 chữ số vì nửa ngày
  //  phép là hợp lệ và `4 - 0.1` trong dấu phẩy động ra `3.9000000000000004`.
  const afterThis = Math.round((data.remaining_days - requestedDays) * 100) / 100

  return (
    <div
      className={cn(
        'rounded-md border px-3 py-2 text-sm',
        enough
          ? 'bg-muted/30'
          : 'border-destructive/50 bg-destructive/5 text-destructive dark:text-destructive-foreground',
      )}
    >
      {/*  BA CON SỐ, MỘT DÒNG. Bản đầu tách ba dòng riêng và cụm đó chiếm gần
           trọn chiều cao hộp trong khi cả ba nói về cùng một quỹ — khách bác
           đúng chỗ đó. Ba mảnh, mảnh nào không có số thì không dựng:
             · quỹ còn lại  — luôn có;
             · CHỜ DUYỆT    — phần giữ chỗ, phải nói ra vì nó đã bị trừ khỏi «còn
               lại» rồi; im thì người ta thấy hụt ngày và tưởng máy tính sai;
             · TRỪ ĐƠN NÀY  — nhẩm hộ người dùng; nhẩm sai thì họ nộp một tờ đơn
               sẽ bị chặn. Vượt quỹ thì bỏ, số âm ở đây vô nghĩa và đã có câu
               cảnh báo riêng bên dưới. */}
      <div className="flex items-center gap-2">
        {!enough && <AlertTriangle className="size-4 shrink-0" />}
        <span>
          Phép năm {year}: còn{' '}
          <strong className="tabular-nums">{data.remaining_days}</strong>/{data.total_days} ngày
          {data.pending_days > 0 && (
            <span className="text-muted-foreground">
              {' · chờ duyệt '}
              <span className="tabular-nums">{data.pending_days}</span>
            </span>
          )}
          {enough && requestedDays > 0 && (
            <span className="text-muted-foreground">
              {' · trừ đơn này '}
              <span className="tabular-nums">{requestedDays}</span>
              {' còn '}
              <strong className="tabular-nums text-foreground">{afterThis}</strong>
            </span>
          )}
        </span>
      </div>

      {!enough && (
        <p className="mt-1 text-xs font-medium">
          Đơn này xin {requestedDays} ngày — vượt quỹ nên sẽ bị chặn lúc gửi duyệt. Muốn nghỉ
          tiếp thì chọn loại «Nghỉ không lương».
        </p>
      )}

      {data.missing_hire_date && (
        //  Q4 của kế hoạch — hồ sơ chưa nhập ngày vào làm thì thâm niên tính
        //  bằng 0, tức con số trên có thể THIẾU. Im lặng là để sai số nằm trong
        //  sổ cả năm không ai biết.
        <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
          Hồ sơ chưa có ngày vào làm nên chưa cộng ngày thâm niên. Báo phòng Nhân sự nhập bổ sung.
        </p>
      )}
    </div>
  )
}
