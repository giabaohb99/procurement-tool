import { Loader2, Scale } from 'lucide-react'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { useOffsetPrepay } from '../hooks/use-payables'
import { usePrepayHanging } from '../hooks/use-payment-requests'
import type { Payable } from '../types/payable'

interface PayableOffsetPrepayDialogProps {
  /** Khoản nợ đang cấn trừ — `null` là đóng hộp thoại. */
  payable: Payable | null
  onClose: () => void
}

/**
 * CR-268 — cấn trừ TIỀN TREO CẤP NCC (phiếu trả trước KHÔNG gắn đơn) vào một
 * khoản công nợ. Đây là thao tác TAY của kế toán: treo gắn đơn thì hệ thống tự
 * đối trừ lúc nhận hàng rồi, không hiện ở đây.
 *
 * Số tiền để trống / 0 = trừ TỐI ĐA. Backend luôn kẹp `min(treo còn, nợ còn)`
 * nên nhập lố cũng không làm công nợ âm — đây chỉ là bản hiển thị cho êm.
 */
export function PayableOffsetPrepayDialog({ payable, onClose }: PayableOffsetPrepayDialogProps) {
  const open = payable !== null
  const [amountText, setAmountText] = useState('')

  // Mở cho khoản khác -> xóa số đã gõ của lần trước.
  const payableChanged = useHasChanged(payable?.id)
  if (payableChanged) setAmountText('')

  // CHỈ treo cấp NCC (`unlinked: 1`) — treo gắn đơn để hệ thống tự xử.
  const { data: hangingData, isLoading } = usePrepayHanging(
    { supplier_code: payable?.supplier_code ?? '', unlinked: 1, source_type: payable?.source_type },
    { enabled: open },
  )
  const offsetPrepay = useOffsetPrepay()

  const hangingTotal = hangingData?.total ?? 0
  const remaining = payable?.remaining ?? 0
  const maxTake = useMemo(() => Math.min(hangingTotal, remaining), [hangingTotal, remaining])
  const amount = Number(amountText) || 0

  async function submit() {
    if (!payable) return
    if (amount < 0) {
      toast.error('Số tiền cấn trừ không được âm')
      return
    }
    if (amount > maxTake + 0.01) {
      toast.error(`Chỉ cấn trừ được tối đa ${formatMoney(maxTake)} đ (min của treo còn và nợ còn)`)
      return
    }
    await offsetPrepay.mutateAsync({ payableId: payable.id, amount })
    onClose()
  }

  return (
    <Dialog open={open} onOpenChange={(next) => !next && onClose()}>
      <DialogContent className="sm:max-w-[560px]">
        <DialogHeader>
          <DialogTitle>Cấn trừ tiền treo trả trước</DialogTitle>
          <DialogDescription>
            Trừ tiền đã trả trước cho NCC <b>{payable?.supplier_name || payable?.supplier_code}</b>{' '}
            (phiếu không gắn đơn) vào khoản nợ này.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <Skeleton className="h-24 w-full" />
        ) : hangingTotal <= 0.01 ? (
          <p className="rounded-md border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
            Nhà cung cấp này không còn tiền treo trả trước (không gắn đơn) để cấn trừ. Tiền treo
            GẮN ĐƠN sẽ tự đối trừ khi đơn đó nhận hàng, không cần thao tác ở đây.
          </p>
        ) : (
          <div className="space-y-3 text-sm">
            <dl className="grid gap-2 rounded-md border bg-muted/30 px-3 py-2 sm:grid-cols-3">
              <div>
                <dt className="text-xs text-muted-foreground">Tiền treo còn lại</dt>
                <dd className="font-semibold text-navy tabular-nums dark:text-foreground">
                  {formatMoney(hangingTotal)} đ
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Nợ còn lại</dt>
                <dd className="font-semibold tabular-nums text-destructive">
                  {formatMoney(remaining)} đ
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Cấn trừ tối đa</dt>
                <dd className="font-semibold tabular-nums">{formatMoney(maxTake)} đ</dd>
              </div>
            </dl>

            {/* Liệt kê từng phiếu treo để kế toán biết tiền đến từ đâu — trừ theo
                thứ tự phiếu CŨ TRƯỚC (FIFO), không chọn từng phiếu được. */}
            <div className="max-h-40 space-y-1 overflow-y-auto">
              {(hangingData?.items ?? []).map((item) => (
                <p
                  key={item.line_id}
                  className="flex items-center justify-between gap-2 rounded border px-2 py-1 text-xs"
                >
                  <span className="text-muted-foreground">
                    {item.request_code} · {formatDate(item.request_date) || '—'}
                  </span>
                  <span className="font-medium tabular-nums">{formatMoney(item.hanging)} đ</span>
                </p>
              ))}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="offset-amount">Số tiền cấn trừ</Label>
              <Input
                id="offset-amount"
                type="number"
                min={0}
                value={amountText}
                placeholder={`Để trống = trừ tối đa ${formatMoney(maxTake)} đ`}
                onChange={(event) => setAmountText(event.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Trừ vào phiếu treo cũ nhất trước. Không bao giờ trừ quá số nợ còn lại.
              </p>
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Đóng
          </Button>
          <Button
            disabled={hangingTotal <= 0.01 || offsetPrepay.isPending}
            onClick={() => void submit()}
          >
            {offsetPrepay.isPending ? <Loader2 className="animate-spin" /> : <Scale />}
            Cấn trừ
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
