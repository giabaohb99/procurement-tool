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

  return (
    <div
      className={cn(
        'rounded-md border px-3 py-2 text-sm',
        enough
          ? 'bg-muted/30'
          : 'border-destructive/50 bg-destructive/5 text-destructive dark:text-destructive-foreground',
      )}
    >
      <div className="flex items-center gap-2">
        {!enough && <AlertTriangle className="size-4 shrink-0" />}
        <span>
          Phép còn lại năm {year}:{' '}
          <strong className="tabular-nums">{data.remaining_days}</strong> / {data.total_days} ngày
        </span>
      </div>

      {data.pending_days > 0 && (
        //  Phần GIỮ CHỖ phải nói ra: nó đã bị trừ khỏi «còn lại» rồi. Không nói
        //  thì người ta thấy hụt ngày và tưởng hệ thống tính sai.
        <p className="mt-0.5 text-xs text-muted-foreground">
          Đã trừ {data.pending_days} ngày của đơn đang chờ duyệt.
        </p>
      )}

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
