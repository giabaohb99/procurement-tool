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
           phép tính lại nằm xa nhau tới mức không còn thấy chúng liên quan.

           ⚠️ **Hai cột ở khổ hẹp, không phải một.** Xếp chồng một cột thì mỗi ô
           là một khung trắng cao 90px cho đúng một con số hai chữ số, bốn ô ăn
           hết 360px màn hình — và cái mất lớn hơn chỗ: bốn số này là một PHÉP
           TÍNH, xếp dọc rời nhau thì không còn đọc ra là chúng cộng vào nhau
           (khách báo 09/09/2026). Hai cột giữ được hình khối của phép tính. */}
      <CardContent className="space-y-5 px-4 sm:px-6">
        {/*  Vế CỘNG — những gì được cấp. */}
        <div>
          <p className="mb-2 text-xs font-medium text-muted-foreground">Được cấp</p>
          <dl className="grid max-w-4xl grid-cols-2 gap-2.5 sm:grid-cols-4 sm:gap-3">
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
          <dl className="grid max-w-4xl grid-cols-2 gap-2.5 sm:grid-cols-4 sm:gap-3">
            <Stat label="Đã nghỉ" value={balance.used_days} />
            <Stat
              label="Chờ duyệt (đang giữ chỗ)"
              value={balance.pending_days}
              valueClassName="text-amber-600 dark:text-amber-400"
            />
            {/*  Chỉ mọc khi ĐÃ kết sổ. Bày ô «Đã chuyển đi: 0» quanh năm cho mọi
                 dòng quỹ là thêm một con số không nói gì vào đúng chỗ người ta
                 đang lần theo phép tính. */}
            {balance.carried_out_days > 0 && (
              <Stat label="Đã chuyển sang năm sau" value={balance.carried_out_days} />
            )}
            {/*  ⚠️ KHÔNG `text-primary`: primary là navy — đúng màu nút hành
                 động chính — nên con số đọc ra như một cái link bấm được.

                 `col-span-2` ở khổ hẹp: đây là KẾT QUẢ của phép tính, không phải
                 một số hạng nữa. Để nó nằm cùng cỡ cùng hàng với các số hạng thì
                 con số người ta mở màn này ra để xem lại là con số khó nhận ra
                 nhất. Trải hết hàng thì nó đứng riêng một dòng dưới cùng, đúng
                 chỗ dấu «=» của phép tính. */}
            <Stat
              label="Còn lại"
              value={balance.remaining_days}
              big
              cellClassName="col-span-2 sm:col-span-1"
              valueClassName={cn(
                balance.remaining_days <= 0 ? 'text-destructive' : 'text-foreground',
              )}
            />
          </dl>

          {/*  Phần HẾT HẠN đứng ngoài phép tính, và phải nói thành câu: nó không
               nằm trong công thức còn lại (đã bị trừ khỏi «Chuyển năm trước»),
               nên đặt nó thành một ô số nữa là mời người đọc cộng nhầm. */}
          {balance.carried_expired_days > 0 && (
            <p className="mt-3 text-sm text-muted-foreground">
              <strong className="tabular-nums text-foreground">
                {balance.carried_expired_days}
              </strong>{' '}
              ngày chuyển từ năm trước đã hết hạn và không dùng được nữa.
            </p>
          )}
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
  cellClassName,
  valueClassName,
}: {
  label: string
  value: number
  /** Thêm dấu `+` khi dương. Số âm tự mang dấu `-`, không ghép tay. */
  signed?: boolean
  big?: boolean
  /** Lớp cho cả Ô — chỗ khai `col-span` khi một số hạng cần trải rộng. */
  cellClassName?: string
  /** Lớp cho riêng CON SỐ — màu theo nghĩa (hổ phách, đỏ…). */
  valueClassName?: string
}) {
  const prefix = signed && value > 0 ? '+' : ''
  return (
    <div className={cn('min-w-0 rounded-md border bg-muted/20 px-3 py-2', cellClassName)}>
      {/*  Nhãn ngắt dòng được: ở hai cột trên màn 390px mỗi ô còn ~160px, mà
           «Chờ duyệt (đang giữ chỗ)» dài hơn thế. */}
      <dt className="text-xs break-words text-muted-foreground">{label}</dt>
      <dd
        className={cn(
          'mt-0.5 font-semibold tabular-nums',
          big ? 'text-2xl' : 'text-lg',
          valueClassName,
        )}
      >
        {`${prefix}${value}`}
      </dd>
    </div>
  )
}
