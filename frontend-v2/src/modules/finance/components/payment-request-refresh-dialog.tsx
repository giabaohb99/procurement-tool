import { ArrowRight, Info, Loader2, RefreshCw } from 'lucide-react'
import { useRef } from 'react'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Skeleton } from '@/shared/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import {
  usePaymentRequestRefreshPreview,
  useRefreshPaymentRequestFromPayables,
} from '../hooks/use-payment-requests'
import type { PaymentRefreshLine, PaymentRefreshState } from '../types/payment-request'

interface PaymentRequestRefreshDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  paymentRequestId: number
  /**
   * Người dùng có quyền ghi phiếu không (`payment_request.write`). Sai thì hộp thoại
   * chỉ để XEM chênh lệch — người duyệt mở từ dải cảnh báo của phiếu đã khóa.
   */
  canWrite: boolean
}

/** Dòng nào phải đập vào mắt: số về 0 vì nợ đã hết / mất, hoặc trùng khoản nợ. */
const ALERT_STATES: PaymentRefreshState[] = ['paid_off', 'payable_missing', 'duplicate']

/**
 * bao-CR-509 — hộp thoại «Cập nhật theo công nợ»: XEM TRƯỚC số cũ → số mới từng dòng
 * rồi mới ghi. Mọi con số và câu lý do đều do backend tính (`service.plan_refresh`);
 * bấm Cập nhật không gửi số nào lên — backend tính lại từ DB lúc ghi.
 */
export function PaymentRequestRefreshDialog({
  open,
  onOpenChange,
  paymentRequestId,
  canWrite,
}: PaymentRequestRefreshDialogProps) {
  const { data: plan, isLoading, isError } = usePaymentRequestRefreshPreview(paymentRequestId, {
    enabled: open,
  })
  const apply = useRefreshPaymentRequestFromPayables(paymentRequestId)
  // `disabled={isPending}` chỉ đúng từ lượt render sau — bấm đúp nhanh vẫn ra hai
  // request. Chốt bằng ref đổi ngay trong tick (bẫy biểu mẫu duoc-CR-317).
  const applyingRef = useRef(false)

  const allowApply = canWrite && Boolean(plan?.can_apply)
  const hasChanges = (plan?.changed_count ?? 0) > 0

  async function handleApply() {
    if (applyingRef.current) return
    applyingRef.current = true
    try {
      await apply.mutateAsync()
      onOpenChange(false)
    } catch {
      // httpClient đã tự toast lỗi non-GET — không toast lại ở đây.
    } finally {
      applyingRef.current = false
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[960px]">
        <DialogHeader>
          <DialogTitle>Cập nhật theo công nợ</DialogTitle>
          <DialogDescription>
            So số đề nghị trên phiếu với nợ còn lại hiện tại của công nợ (đã trừ phần cấn trừ trả
            trước nếu có). Soát lại rồi bấm <b>Cập nhật</b> — thay đổi chưa Lưu trên màn hình sẽ bị
            thay bằng số mới.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <Skeleton className="h-40 w-full" />
        ) : isError || !plan ? (
          <p className="text-sm text-destructive">Không tải được bản xem trước. Thử đóng rồi mở lại.</p>
        ) : (
          <div className="space-y-3">
            {!plan.can_apply && plan.blocked_reason && (
              <p className="flex items-start gap-2 rounded-md border border-warning/30 bg-warning/5 px-3 py-2 text-sm text-warning">
                <Info className="mt-0.5 size-4 shrink-0" />
                <span>{plan.blocked_reason}</span>
              </p>
            )}
            {!hasChanges && (
              <p className="flex items-start gap-2 rounded-md border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
                <Info className="mt-0.5 size-4 shrink-0" />
                <span>Phiếu đã khớp công nợ hiện tại, không có dòng nào cần đổi.</span>
              </p>
            )}
            <Table containerClassName="max-h-[55vh] rounded-md border">
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10">#</TableHead>
                  <TableHead>PO</TableHead>
                  <TableHead>Số HĐ</TableHead>
                  <TableHead>Ngày HĐ</TableHead>
                  <TableHead className="text-right">Số cũ → Số mới</TableHead>
                  <TableHead>Lý do</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {plan.lines.map((line) => (
                  <RefreshLineRow key={line.line_id} line={line} />
                ))}
              </TableBody>
            </Table>
            <p className="text-right text-base text-navy dark:text-foreground">
              Tổng đề nghị thanh toán:{' '}
              <span className="tabular-nums">{formatMoney(plan.old_total)}</span>
              <ArrowRight className="mx-1.5 inline size-4 text-muted-foreground" />
              <b className="tabular-nums">{formatMoney(plan.new_total)}</b>
            </p>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {allowApply ? 'Hủy' : 'Đóng'}
          </Button>
          {allowApply && (
            <Button onClick={() => void handleApply()} disabled={apply.isPending || !hasChanges}>
              {apply.isPending ? <Loader2 className="animate-spin" /> : <RefreshCw />}
              Cập nhật
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

/** Hai giá trị cũ/mới: giống nhau thì in một, khác thì in «cũ → mới». */
function OldNew({ oldValue, newValue }: { oldValue: string; newValue: string }) {
  if (oldValue === newValue) return <>{newValue || '—'}</>
  return (
    <span>
      <span className="text-muted-foreground line-through">{oldValue || '—'}</span>
      <ArrowRight className="mx-1 inline size-3.5 text-muted-foreground" />
      <b>{newValue || '—'}</b>
    </span>
  )
}

function RefreshLineRow({ line }: { line: PaymentRefreshLine }) {
  const alert = ALERT_STATES.includes(line.state) && line.amount_old > 0.01
  return (
    <TableRow className={cn(alert && 'bg-destructive/5', line.state === 'manual' && 'text-muted-foreground')}>
      <TableCell>{line.index}</TableCell>
      <TableCell>
        <OldNew oldValue={line.po_code_old} newValue={line.po_code_new} />
      </TableCell>
      <TableCell>
        <OldNew oldValue={line.invoice_no_old} newValue={line.invoice_no_new} />
      </TableCell>
      <TableCell>
        <OldNew oldValue={formatDate(line.invoice_date_old)} newValue={formatDate(line.invoice_date_new)} />
      </TableCell>
      <TableCell className="text-right tabular-nums">
        {line.amount_changed ? (
          <>
            <span className="text-muted-foreground line-through">{formatMoney(line.amount_old)}</span>
            <ArrowRight className="mx-1 inline size-3.5 text-muted-foreground" />
            <b className={cn(alert && 'text-destructive')}>{formatMoney(line.amount_new)}</b>
          </>
        ) : (
          formatMoney(line.amount_new)
        )}
      </TableCell>
      <TableCell className={cn('min-w-56 whitespace-normal text-sm', alert && 'text-destructive')}>
        {line.reason}
      </TableCell>
    </TableRow>
  )
}
