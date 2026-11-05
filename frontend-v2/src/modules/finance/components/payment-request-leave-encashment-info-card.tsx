import { ExternalLink } from 'lucide-react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { LEAVE_ENCASHMENT_REASON_LABELS } from '@/modules/hr/types/leave-encashment'
import { appRoutes } from '@/shared/constants/app-routes'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Label } from '@/shared/ui/label'
import { NumberInput } from '@/shared/ui/number-input'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import {
  MAX_PAYOUT_AMOUNT,
  PAYMENT_METHOD_LABELS,
  type PaymentMethod,
  type PaymentRequest,
} from '../types/payment-request'

interface PaymentRequestLeaveEncashmentInfoCardProps {
  req: PaymentRequest
  companyName: string
  editable: boolean
  amount: number
  onAmountChange: (value: number) => void
  paymentMethod: PaymentMethod
  onPaymentMethodChange: (value: PaymentMethod) => void
  note: string
  onNoteChange: (value: string) => void
}

/**
 * Thẻ "Thông tin phiếu" của YCTT THANH TOÁN NGHỈ PHÉP (duoc-CR-719). Người nhận là NHÂN SỰ (tên + mã, không số tài
 * khoản — STK chỉ in theo D2a), phiếu nguồn `TTP…`, số ngày / loại / năm / lý do, và ô Số tiền — ô DUY NHẤT về tiền,
 * vì phiếu chỉ có đúng một dòng (backend chặn thêm / bớt dòng).
 */
export function PaymentRequestLeaveEncashmentInfoCard({
  req,
  companyName,
  editable,
  amount,
  onAmountChange,
  paymentMethod,
  onPaymentMethodChange,
  note,
  onNoteChange,
}: PaymentRequestLeaveEncashmentInfoCardProps) {
  const { can } = usePermission()
  const source = req.leave_encashment

  return (
    <Card className="gap-4 py-4">
      <CardHeader className="min-h-9 border-b px-4 pb-3!">
        <CardTitle className="text-base text-navy dark:text-foreground">Thông tin phiếu</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 px-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="space-y-1.5">
          <Label>Người nhận</Label>
          <ReadOnlyValue>{req.supplier_name || '—'}</ReadOnlyValue>
        </div>
        <div className="space-y-1.5">
          <Label>Phiếu thanh toán nghỉ phép</Label>
          {source && can('leave_encashment', 'read') ? (
            <ReadOnlyValue>
              <Link
                to={appRoutes.hr.leaveEncashmentDetail(source.id)}
                className="inline-flex items-center gap-1 text-primary hover:underline"
              >
                {source.code}
                <ExternalLink className="size-3.5" />
              </Link>
            </ReadOnlyValue>
          ) : (
            <ReadOnlyValue>{source?.code || '—'}</ReadOnlyValue>
          )}
        </div>
        <div className="space-y-1.5">
          <Label>Nội dung</Label>
          <ReadOnlyValue>
            {source
              ? `${String(source.days).replace('.', ',')} ngày ${source.leave_type_name} năm ${source.balance_year} · ${LEAVE_ENCASHMENT_REASON_LABELS[source.reason_kind] ?? ''}`
              : '—'}
          </ReadOnlyValue>
        </div>
        <div className="space-y-1.5">
          <Label>Công ty</Label>
          <ReadOnlyValue>{companyName}</ReadOnlyValue>
        </div>
        <div className="space-y-1.5">
          <Label>Ngày lập</Label>
          <ReadOnlyValue>{formatDate(req.request_date)}</ReadOnlyValue>
        </div>
        <div className="space-y-1.5">
          <Label>Hình thức thanh toán</Label>
          {editable ? (
            <Select value={paymentMethod} onValueChange={(v) => onPaymentMethodChange(v as PaymentMethod)}>
              <SelectTrigger className="w-full" aria-label="Hình thức thanh toán">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(PAYMENT_METHOD_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <ReadOnlyValue>{PAYMENT_METHOD_LABELS[req.payment_method] ?? req.payment_method}</ReadOnlyValue>
          )}
          <p className="text-xs text-muted-foreground">
            Chuyển khoản: bản in lấy số tài khoản trên hồ sơ nhân sự nếu bạn được xem, không thì để kế toán tự điền.
          </p>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="payout-amount">Số tiền thanh toán</Label>
          {editable ? (
            <NumberInput
              id="payout-amount"
              value={amount}
              onChange={onAmountChange}
              decimals={false}
              max={MAX_PAYOUT_AMOUNT}
              placeholder="Nhập số tiền"
            />
          ) : (
            <ReadOnlyValue>{formatMoney(req.total)}</ReadOnlyValue>
          )}
          {editable && (
            <p className={cn('text-xs', amount > 0 ? 'text-muted-foreground' : 'text-warning')}>
              {amount > 0
                ? 'Nhớ bấm Lưu (hoặc Gửi duyệt) sau khi nhập.'
                : 'Phiếu sinh ra với số tiền 0 — nhập số tiền rồi mới gửi duyệt được.'}
            </p>
          )}
        </div>
        <div className="space-y-1.5 sm:col-span-2 lg:col-span-3">
          <Label htmlFor="payout-note">Ghi chú</Label>
          {editable ? (
            <Textarea id="payout-note" value={note} onChange={(e) => onNoteChange(e.target.value)} />
          ) : (
            <ReadOnlyValue multiline>{req.note}</ReadOnlyValue>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
