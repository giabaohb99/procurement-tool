import { formatDate } from '@/shared/utils/format-date'
import type { LeaveRequest } from '../types/leave'
import { formatRequestPeriods, periodsOf } from '../utils/leave-periods'

/**
 * Ô «Đến ngày» của bảng đơn nghỉ (duoc-CR-683).
 *
 * Hai cột Từ/Đến ngày là BAO NGOÀI của đơn — đơn nhiều khoảng thì giữa hai mốc đó có ngày đi
 * làm. Ô bảng cao 35px không đủ chỗ kê từng khoảng, nên chỉ thêm chữ mờ «· 2 khoảng» để người
 * đọc biết đây không phải một đợt liền; rê chuột vào ô thì `title` kê đủ các khoảng, trình đọc màn hình đọc bản `sr-only`.
 */
export function LeaveToDateCell({ request }: { request: LeaveRequest }) {
  const count = periodsOf(request).length
  if (count < 2) return <span className="tabular-nums">{formatDate(request.to_date)}</span>
  const text = formatRequestPeriods(request)
  //  `title` chỉ tới tay người rê chuột — trình đọc màn hình và màn cảm ứng không nhận. Kê lại
  //  danh sách khoảng bằng chữ `sr-only` để trình đọc màn hình đọc được (L9 của duoc-CR-683).
  return (
    <span className="tabular-nums" title={text}>
      {formatDate(request.to_date)}
      <span className="text-muted-foreground" aria-hidden="true">{` · ${count} khoảng`}</span>
      <span className="sr-only">{`, gồm ${count} khoảng: ${text}`}</span>
    </span>
  )
}
