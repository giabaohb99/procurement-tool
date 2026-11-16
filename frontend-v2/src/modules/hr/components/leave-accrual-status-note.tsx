import { CalendarClock, TriangleAlert } from 'lucide-react'

import { formatDate } from '@/shared/utils/format-date'
import { LEAVE_ACCRUAL_STATUS, type LeaveAccrualInfo } from '../types/leave'
import { getAccrualTone, getContractActionHint } from '../utils/leave-accrual-status'

/**
 * Dải giải thích tình trạng tích phép ở TRANG CHI TIẾT dòng quỹ (duoc-CR-762, loại `MONTHLY_AFTER`).
 *
 * Bảng chỉ có nhãn ngắn + gợi ý rê chuột; ở đây nói thành câu đủ vì máy cảm ứng không rê chuột được, và đây là chỗ
 * Nhân sự mở ra khi hỏi *"sao người này còn ít thế"*. Chữ tình trạng là `accrual_status_label` của API; ở đây chỉ thêm
 * ngày và việc cần làm. Loại nghỉ chế độ khác (cả ba trường `null`) → không dựng gì.
 */
export function LeaveAccrualStatusNote({ info }: { info: LeaveAccrualInfo }) {
  const start = formatDate(info.accrual_start_date)
  const tone = getAccrualTone(info.accrual_status)
  const label = info.accrual_status_label?.trim()

  if (tone === 'warn' && label) {
    //  Mã 3: câu chốt có ngày vào làm. Mã 4: nhãn API đã nói "đang tính từ ngày vào làm", chỉ thêm ngày + việc cần làm.
    const text =
      info.accrual_status === LEAVE_ACCRUAL_STATUS.MISSING_CONTRACT
        ? `${label} — phép đang tính từ ngày vào làm${start ? ` ${start}` : ''}. Nhập hợp đồng lao động để tính đúng.`
        : `${label}${start ? ` (${start})` : ''}. ${getContractActionHint(info.accrual_status)}.`
    return (
      <p className="flex items-start gap-2 rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-sm text-foreground">
        <TriangleAlert className="mt-0.5 size-4 shrink-0 text-amber-600 dark:text-amber-400" />
        <span>{text}</span>
      </p>
    )
  }

  if (tone === 'muted' && label) {
    return (
      <p className="flex items-start gap-2 rounded-md border bg-muted/30 px-3 py-2 text-sm text-muted-foreground">
        <CalendarClock className="mt-0.5 size-4 shrink-0" />
        {label}.
      </p>
    )
  }

  if (tone === 'none' && start) {
    return (
      <p className="flex items-start gap-2 rounded-md border bg-muted/30 px-3 py-2 text-sm text-muted-foreground">
        <CalendarClock className="mt-0.5 size-4 shrink-0" />
        Tích từ {start} — làm xong tháng nào được cộng phần của tháng đó.
      </p>
    )
  }

  return null
}
