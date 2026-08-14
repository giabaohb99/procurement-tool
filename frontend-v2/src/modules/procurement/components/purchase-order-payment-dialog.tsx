import { Loader2, Receipt } from 'lucide-react'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Skeleton } from '@/shared/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { Tabs, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import {
  useCreatePaymentRequest,
  usePurchaseOrderPayables,
} from '../hooks/use-purchase-order-payment'

/** Hai luồng công nợ tách bạch: tiền hàng và cước vận chuyển (khác nhà cung cấp). */
const SOURCE_TABS = [
  { value: 'goods', label: 'NCC sản xuất (hàng)' },
  { value: 'shipping', label: 'NCC vận chuyển' },
] as const

const PAYMENT_METHODS = [
  { value: 'transfer', label: 'Chuyển khoản' },
  { value: 'cash', label: 'Tiền mặt' },
] as const

interface PurchaseOrderPaymentDialogProps {
  open: boolean
  purchaseOrderCode: string
  onOpenChange: (open: boolean) => void
}

/**
 * Tạo Yêu cầu thanh toán từ ĐMH: chọn các khoản công nợ CHƯA TRẢ ĐỦ của đơn.
 *
 * Mặc định chỉ tick sẵn công nợ HÀNG — cước vận chuyển thường thanh toán theo
 * kỳ với đơn vị vận chuyển khác nên để người dùng chủ động chọn thêm.
 * Backend tự tách mỗi nhà cung cấp thành một phiếu riêng.
 */
export function PurchaseOrderPaymentDialog({
  open,
  purchaseOrderCode,
  onOpenChange,
}: PurchaseOrderPaymentDialogProps) {
  const { data, isLoading } = usePurchaseOrderPayables(purchaseOrderCode, open)
  const createPaymentRequest = useCreatePaymentRequest()

  const [tab, setTab] = useState<'goods' | 'shipping'>('goods')
  const [selected, setSelected] = useState<number[]>([])
  const [note, setNote] = useState('')
  const [method, setMethod] = useState<string>('transfer')

  /** Chỉ những khoản còn nợ mới có việc để làm. */
  const payables = useMemo(
    () => (data?.items ?? []).filter((payable) => payable.remaining > 0.01),
    [data?.items],
  )

  // Mở hộp thoại (hoặc danh sách công nợ đổi) -> dựng lại lựa chọn mặc định.
  // Gọi hook ra biến riêng: `||` sẽ short-circuit, làm hook thứ hai không chạy.
  const openChanged = useHasChanged(open)
  const payablesChanged = useHasChanged(payables)
  if (openChanged || payablesChanged) {
    const goods = payables.filter((payable) => payable.source_type === 'goods')
    setSelected(goods.map((payable) => payable.id))
    setTab(goods.length ? 'goods' : 'shipping')
    setNote('')
    setMethod('transfer')
  }

  const rows = payables.filter((payable) => payable.source_type === tab)
  const allChecked = rows.length > 0 && rows.every((row) => selected.includes(row.id))
  const total = payables
    .filter((payable) => selected.includes(payable.id))
    .reduce((sum, payable) => sum + payable.remaining, 0)

  function toggleAll(checked: boolean) {
    const ids = rows.map((row) => row.id)
    setSelected((current) =>
      checked
        ? Array.from(new Set([...current, ...ids]))
        : current.filter((id) => !ids.includes(id)),
    )
  }

  async function submit() {
    if (!selected.length) {
      toast.error('Chưa chọn khoản công nợ nào')
      return
    }
    await createPaymentRequest.mutateAsync({
      request_date: new Date().toISOString().slice(0, 10),
      note,
      payment_method: method,
      lines: payables
        .filter((payable) => selected.includes(payable.id))
        .map((payable) => ({ payable_id: payable.id, amount: payable.remaining })),
    })
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] w-[96vw] overflow-y-auto sm:max-w-[900px]">
        <DialogHeader>
          <DialogTitle>Tạo yêu cầu thanh toán — chọn hóa đơn</DialogTitle>
          <DialogDescription>
            Công nợ chưa trả đủ của đơn <b>{purchaseOrderCode}</b>. Mỗi lần nhận hàng là một
            dòng; cùng số hóa đơn có thể có nhiều dòng.
          </DialogDescription>
        </DialogHeader>

        <Tabs value={tab} onValueChange={(value) => setTab(value as 'goods' | 'shipping')}>
          <TabsList>
            {SOURCE_TABS.map((source) => {
              const count = payables.filter(
                (payable) => payable.source_type === source.value,
              ).length
              return (
                <TabsTrigger key={source.value} value={source.value}>
                  {source.label}
                  {count ? ` (${count})` : ''}
                </TabsTrigger>
              )
            })}
          </TabsList>
        </Tabs>

        {isLoading ? (
          <Skeleton className="h-40 w-full" />
        ) : (
          <div className="overflow-x-auto rounded-lg border">
            <Table>
              <TableHeader className="bg-muted">
                <TableRow>
                  <TableHead className="w-12 text-center">
                    <Checkbox
                      checked={allChecked}
                      onCheckedChange={(checked) => toggleAll(checked === true)}
                      aria-label="Chọn tất cả"
                    />
                  </TableHead>
                  <TableHead>
                    {tab === 'goods' ? 'Nhà cung cấp' : 'Đơn vị vận chuyển'}
                  </TableHead>
                  <TableHead className="w-40">Số hóa đơn</TableHead>
                  <TableHead className="w-32">Ngày phát sinh</TableHead>
                  <TableHead className="w-32 text-right">Phải trả</TableHead>
                  <TableHead className="w-32 text-right">Đã trả</TableHead>
                  <TableHead className="w-32 text-right">Còn lại</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} className="h-20 text-center text-muted-foreground">
                      Không có khoản nợ nào cần thanh toán.
                    </TableCell>
                  </TableRow>
                )}
                {rows.map((payable) => (
                  <TableRow key={payable.id}>
                    <TableCell className="text-center">
                      <Checkbox
                        checked={selected.includes(payable.id)}
                        onCheckedChange={(checked) =>
                          setSelected((current) =>
                            checked === true
                              ? [...current, payable.id]
                              : current.filter((id) => id !== payable.id),
                          )
                        }
                        aria-label={`Chọn hóa đơn ${payable.invoice_no || payable.id}`}
                      />
                    </TableCell>
                    <TableCell className="whitespace-normal">
                      {payable.supplier_name || payable.supplier_code || '—'}
                    </TableCell>
                    <TableCell>{payable.invoice_no || '—'}</TableCell>
                    <TableCell>{formatDate(payable.incur_date) || '—'}</TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatMoney(payable.total)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums text-success">
                      {formatMoney(payable.paid_amount)}
                    </TableCell>
                    <TableCell className="text-right font-semibold tabular-nums text-destructive">
                      {formatMoney(payable.remaining)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}

        <div className="grid gap-3 md:grid-cols-2">
          <div className="space-y-1.5">
            <Label>Hình thức thanh toán</Label>
            <Select value={method} onValueChange={setMethod}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PAYMENT_METHODS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Ghi chú</Label>
            <Input
              value={note}
              placeholder="Nội dung đề nghị thanh toán…"
              onChange={(event) => setNote(event.target.value)}
            />
          </div>
        </div>

        <DialogFooter className="sm:justify-between">
          <span className="text-sm text-navy dark:text-foreground">
            Đã chọn {selected.length} khoản · Tổng đề nghị:{' '}
            <b className="tabular-nums">{formatMoney(total)} đ</b>
          </span>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Đóng
            </Button>
            <Button
              disabled={!selected.length || createPaymentRequest.isPending}
              onClick={() => void submit()}
            >
              {createPaymentRequest.isPending ? (
                <Loader2 className="animate-spin" />
              ) : (
                <Receipt />
              )}
              Tạo yêu cầu thanh toán
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
