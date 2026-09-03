import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { cn } from '@/shared/utils/cn'
import type { LeaveBalance } from '../types/leave'

interface LeaveBalanceBreakdownCardProps {
  balance: LeaveBalance
}

/**
 * PHÂN RÃ quỹ phép: con số «còn lại» được cấu thành từ đâu.
 *
 * ⚠️ Bày ra thành phép tính chứ không chỉ liệt kê. Người xem đến đây với đúng
 * một câu hỏi — *"vì sao còn từng ấy ngày"* — và bảng danh sách chỉ trả lời
 * được nửa: nó cho thấy tám con số nhưng không cho thấy chúng nối với nhau thế
 * nào. Ai không nhớ công thức thì tự cộng, và tự cộng thì cộng sai.
 */
export function LeaveBalanceBreakdownCard({ balance }: LeaveBalanceBreakdownCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Quỹ phép năm {balance.year}</CardTitle>
        <p className="text-sm text-muted-foreground">
          Hạn mức cộng thâm niên và ngày chuyển năm trước, trừ đi số đã nghỉ và số đang giữ
          chỗ cho đơn chờ duyệt.
        </p>
      </CardHeader>

      {/*  `max-w-*` trên từng lưới: không bó thì trên màn 24" mỗi thẻ rộng
           400px cho đúng một con số hai chữ, và bốn con số vốn đọc thành một
           phép tính lại nằm xa nhau tới mức không còn thấy chúng liên quan. */}
      <CardContent className="space-y-5">
        {/*  Vế CỘNG — những gì được cấp. */}
        <div>
          <p className="mb-2 text-xs font-medium text-muted-foreground">Được cấp</p>
          <dl className="grid max-w-4xl gap-3 sm:grid-cols-4">
            <Stat label="Hạn mức" value={balance.allocated_days} />
            <Stat label="Thâm niên" value={balance.seniority_days} signed />
            <Stat label="Chuyển năm trước" value={balance.carried_days} signed />
            <Stat label="Điều chỉnh tay" value={balance.adjusted_days} signed />
          </dl>
          <p className="mt-2 text-sm text-muted-foreground">
            Tổng được nghỉ:{' '}
            <strong className="tabular-nums text-foreground">{balance.total_days}</strong> ngày
          </p>
        </div>

        {/*  Vế TRỪ — những gì đã tiêu hoặc đang bị giữ. */}
        <div className="border-t pt-4">
          <p className="mb-2 text-xs font-medium text-muted-foreground">Đã dùng</p>
          <dl className="grid max-w-3xl gap-3 sm:grid-cols-3">
            <Stat label="Đã nghỉ" value={balance.used_days} />
            <Stat
              label="Chờ duyệt (đang giữ chỗ)"
              value={balance.pending_days}
              className="text-amber-600 dark:text-amber-400"
            />
            {/*  ⚠️ KHÔNG `text-primary`: primary là navy — đúng màu nút hành
                 động chính — nên con số đọc ra như một cái link bấm được. */}
            <Stat
              label="Còn lại"
              value={balance.remaining_days}
              big
              className={cn(
                balance.remaining_days <= 0 ? 'text-destructive' : 'text-foreground',
              )}
            />
          </dl>
        </div>

        {balance.note?.trim() && (
          <p className="border-t pt-4 text-sm break-words text-muted-foreground">
            <span className="font-medium text-foreground">Ghi chú điều chỉnh:</span>{' '}
            {balance.note}
          </p>
        )}
      </CardContent>
    </Card>
  )
}

/**
 * Một con số trong phân rã.
 *
 * ⚠️ Số 0 hiện thành **"0"**, không phải dấu gạch như ngoài bảng danh sách.
 * Ngoài kia dấu gạch để bảng bảy cột bớt đặc; ở đây người đọc đang lần theo một
 * phép tính, và dấu gạch giữa dãy phép tính đọc ra là "không biết" chứ không
 * phải "bằng không".
 */
function Stat({
  label,
  value,
  signed = false,
  big = false,
  className,
}: {
  label: string
  value: number
  /** Thêm dấu `+` khi dương. Số âm tự mang dấu `-`, không ghép tay. */
  signed?: boolean
  big?: boolean
  className?: string
}) {
  const prefix = signed && value > 0 ? '+' : ''
  return (
    <div className="min-w-0 rounded-md border bg-muted/20 px-3 py-2.5">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd
        className={cn(
          'mt-1 font-semibold tabular-nums',
          big ? 'text-2xl' : 'text-lg',
          className,
        )}
      >
        {`${prefix}${value}`}
      </dd>
    </div>
  )
}
