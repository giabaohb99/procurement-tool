import { ExternalLink, Info } from 'lucide-react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { FormSection } from '@/shared/ui/form-section'
import { cn } from '@/shared/utils/cn'
import { formatMoney } from '@/shared/utils/format-money'
import type { EncashmentPayment } from '../types/leave-encashment'

interface LeaveEncashmentPaymentCardProps {
  payment: EncashmentPayment | null | undefined
  /** Lý do backend chặn hủy phiếu (rỗng = hủy được). */
  cancelBlockedReason?: string
}

const STATUS_TONE: Record<EncashmentPayment['status'], string> = {
  draft: 'text-muted-foreground',
  submitted: 'text-sky-700 dark:text-sky-300',
  approved: 'text-sky-700 dark:text-sky-300',
  paid: 'text-emerald-700 dark:text-emerald-300',
  cancelled: 'text-destructive',
}

/**
 * Nhóm THANH TOÁN của phiếu đã duyệt (duoc-CR-719): YCTT nào, đang ở đâu, bao nhiêu tiền. Bố cục phẳng — một
 * `FormSection` như các nhóm khác của trang, không thẻ viền riêng.
 *
 * ⚠️ Số tiền = lương ngày × số ngày nên CHỈ vẽ khi API trả `total` khác null (chính người nhận, hoặc người đọc được
 * YCTT đó — D1a). Không tự tính, không gọi API YCTT. Link sang Tài chính chỉ khi có `payment_request.read`; thiếu quyền
 * thì mã YCTT là chữ thường (bấm vào cũng chỉ ăn 404 theo chốt xem của backend).
 */
export function LeaveEncashmentPaymentCard({ payment, cancelBlockedReason }: LeaveEncashmentPaymentCardProps) {
  const { can } = usePermission()

  return (
    <FormSection title="Thanh toán">
      {payment ? (
        <dl className="col-span-full grid gap-3 text-sm sm:grid-cols-3">
          <div className="space-y-1">
            <dt className="text-xs text-muted-foreground">Yêu cầu thanh toán</dt>
            <dd className="font-medium">
              {can('payment_request', 'read') ? (
                <Link
                  to={appRoutes.finance.paymentRequestDetail(payment.id)}
                  className="inline-flex items-center gap-1 text-primary hover:underline"
                >
                  {payment.code}
                  <ExternalLink className="size-3.5" />
                </Link>
              ) : (
                payment.code
              )}
            </dd>
          </div>
          <div className="space-y-1">
            <dt className="text-xs text-muted-foreground">Trạng thái chi</dt>
            <dd className={cn('font-medium', STATUS_TONE[payment.status])}>{payment.status_label}</dd>
          </div>
          {payment.total !== null && payment.total !== undefined && (
            <div className="space-y-1">
              <dt className="text-xs text-muted-foreground">Số tiền</dt>
              <dd className="font-medium tabular-nums">
                {payment.total > 0 ? (
                  formatMoney(payment.total)
                ) : (
                  <span className="text-muted-foreground">Kế toán chưa nhập</span>
                )}
              </dd>
            </div>
          )}
        </dl>
      ) : (
        <p className="col-span-full text-sm text-muted-foreground">Chưa có yêu cầu thanh toán cho phiếu này.</p>
      )}
      {cancelBlockedReason?.trim() && (
        <p className="col-span-full flex items-start gap-2 text-xs text-muted-foreground">
          <Info className="mt-0.5 size-3.5 shrink-0" />
          <span>Chưa hủy được phiếu: {cancelBlockedReason}.</span>
        </p>
      )}
    </FormSection>
  )
}
