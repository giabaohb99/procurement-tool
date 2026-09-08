import { Info, Loader2, Receipt, TriangleAlert } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
// CR-268: mượn hook tiền treo của phân hệ Tài chính.
import { usePrepayHanging } from '@/modules/finance/hooks/use-payment-requests'
import { appRoutes } from '@/shared/constants/app-routes'
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Skeleton } from '@/shared/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/ui/table'
import { Tabs, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import type { PurchaseOrderDetail } from '../types/purchase-order-detail'
import { buildPrepayPayable } from '../utils/build-prepay-payable'
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
  order: PurchaseOrderDetail
  onOpenChange: (open: boolean) => void
}

/**
 * Tạo Yêu cầu thanh toán từ ĐMH: chọn các khoản công nợ CHƯA TRẢ ĐỦ của đơn.
 *
 * Mặc định chỉ tick sẵn công nợ HÀNG — cước vận chuyển thường thanh toán theo
 * kỳ với đơn vị vận chuyển khác nên để người dùng chủ động chọn thêm.
 * Backend tự tách mỗi nhà cung cấp thành một phiếu riêng.
 *
 * Đơn CHƯA có khoản nợ nào thì hộp thoại đổi hẳn sang luồng **thanh toán TRƯỚC**
 * (CR-067) thay vì báo "không có gì để thanh toán" rồi tắc — xem `PrepayPanel`.
 */
export function PurchaseOrderPaymentDialog({
  open,
  order,
  onOpenChange,
}: PurchaseOrderPaymentDialogProps) {
  const { data, isLoading } = usePurchaseOrderPayables(order.code, open)
  const createPaymentRequest = useCreatePaymentRequest()
  const navigate = useNavigate()
  const { can } = usePermission()

  const [tab, setTab] = useState<'goods' | 'shipping'>('goods')
  const [selected, setSelected] = useState<number[]>([])
  const [note, setNote] = useState('')
  const [method, setMethod] = useState<string>('transfer')
  // CR-268: tick "dùng tiền trả trước để trừ nợ" — bật sẵn vì đó là điều người
  // dùng muốn trong 99% trường hợp (đã đưa tiền rồi thì trừ đi chứ chi thêm làm gì).
  const [useOffset, setUseOffset] = useState(true)

  // CR-260 (thay CR-270): tick cấn trừ chỉ GHI phần cấn trừ vào dòng phiếu — công
  // nợ chưa bị đụng, nên KHÔNG cần `payable.write` ở đây nữa; người DUYỆT phiếu
  // mới là người thực thi. Chỉ cần quyền đọc để hỏi NCC còn treo bao nhiêu.
  const canOffset = can('payment_request', 'read')
  const { data: hangingData } = usePrepayHanging(
    { supplier_code: order.supplier_code ?? '', unlinked: 1 },
    { enabled: open && canOffset },
  )
  const hangingTotal = hangingData?.total ?? 0

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
    setUseOffset(true)
  }

  const rows = payables.filter((payable) => payable.source_type === tab)
  const allChecked = rows.length > 0 && rows.every((row) => selected.includes(row.id))
  const total = payables
    .filter((payable) => selected.includes(payable.id))
    .reduce((sum, payable) => sum + payable.remaining, 0)

  // CR-268: tiền treo cấp NCC chỉ trừ được vào nợ HÀNG của đúng NCC bán hàng —
  // cước vận chuyển là nợ với nhà xe, không dính gì tới tiền đã đưa NCC sản xuất.
  const offsetables = payables.filter(
    (payable) =>
      selected.includes(payable.id) &&
      payable.source_type === 'goods' &&
      payable.supplier_code === order.supplier_code,
  )
  const offsetableTotal = offsetables.reduce((sum, payable) => sum + payable.remaining, 0)
  const offsetApplicable = Math.min(hangingTotal, offsetableTotal)
  const effectiveOffset = useOffset && canOffset ? offsetApplicable : 0
  /** Số thật sự phải chi thêm sau khi trừ tiền trả trước. */
  const payTotal = Math.max(0, total - effectiveOffset)

  function toggleAll(checked: boolean) {
    const ids = rows.map((row) => row.id)
    setSelected((current) =>
      checked
        ? Array.from(new Set([...current, ...ids]))
        : current.filter((id) => !ids.includes(id)),
    )
  }

  /**
   * CR-260 (thay CR-270): tick "dùng tiền trả trước" chỉ GHI phần cấn trừ vào
   * từng dòng phiếu (`offset_amount`) — công nợ CHƯA bị đụng đồng nào. Người
   * duyệt nhìn thấy phần cấn trừ trên chi tiết phiếu, bấm Duyệt backend mới
   * thực thi; bấm nhầm thì xóa nháp là xong, không có gì phải gỡ.
   *
   * Chia treo cho các khoản theo ngày phát sinh sớm trước — khớp luật FIFO mà
   * backend sẽ dùng lúc duyệt, để con số xem trước trùng con số trừ thật.
   */
  function submit() {
    if (!selected.length) {
      toast.error('Chưa chọn khoản công nợ nào')
      return
    }
    const offsets = new Map<number, number>()
    if (effectiveOffset > 0.01) {
      let hangingLeft = hangingTotal
      const targets = [...offsetables].sort(
        (a, b) => (a.incur_date || '').localeCompare(b.incur_date || '') || a.id - b.id,
      )
      for (const payable of targets) {
        if (hangingLeft <= 0.01) break
        const part = Math.min(hangingLeft, payable.remaining)
        offsets.set(payable.id, part)
        hangingLeft -= part
      }
    }

    const lines = payables
      .filter((payable) => selected.includes(payable.id))
      .map((payable) => {
        const offset = offsets.get(payable.id) ?? 0
        return {
          payable_id: payable.id,
          amount: Math.max(0, payable.remaining - offset),
          offset_amount: offset,
        }
      })
      .filter((line) => line.amount > 0.01 || line.offset_amount > 0.01)

    void createPaymentRequest
      .mutateAsync({
        request_date: new Date().toISOString().slice(0, 10),
        note,
        payment_method: method,
        lines,
      })
      .then((requests) => {
        onOpenChange(false)
        // Tạo 1 phiếu -> vào thẳng chi tiết (người dùng bấm Gửi duyệt luôn tại đó);
        // nhiều phiếu (tách theo NCC) -> về danh sách YCTT cho thấy đủ cả cụm.
        if (requests.length === 1) {
          navigate(appRoutes.finance.paymentRequestDetail(requests[0].id))
        } else if (requests.length > 1) {
          navigate(appRoutes.finance.paymentRequests)
        }
      })
      .catch(() => undefined) // httpClient đã tự toast lỗi non-GET.
  }

  /**
   * Sang màn tạo YCTT với MỘT dòng dựng sẵn bằng tổng tiền đơn (CR-067).
   *
   * Đi bằng `state` chứ không ghi thẳng DB: màn tạo YCTT là màn nhập liệu, chỉ
   * ghi khi bấm *Tạo phiếu* (CR-025). Không kèm `?payables=` nên màn đó ở chế độ
   * form trắng — người lập còn sửa được số tiền, số chứng từ, chọn lại công ty.
   */
  function goPrepay() {
    onOpenChange(false)
    navigate(appRoutes.finance.paymentRequestNew, {
      // CR-268: `prepay: true` để màn tạo tick sẵn ô "Thanh toán trước" — phiếu
      // được miễn cổng khớp công nợ và tiền chi ra thành tiền treo chờ đối trừ.
      state: { rows: [buildPrepayPayable(order)], prepay: true },
    })
  }

  // Không còn khoản nợ nào để tick -> đổi hẳn sang luồng thanh toán trước, đừng
  // hiện bảng rỗng rồi để người dùng đứng hình.
  const noPayables = !isLoading && payables.length === 0

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] w-[96vw] overflow-y-auto sm:max-w-[900px]">
        <DialogHeader>
          <DialogTitle>
            {noPayables ? 'Tạo yêu cầu thanh toán trước' : 'Tạo yêu cầu thanh toán — chọn hóa đơn'}
          </DialogTitle>
          <DialogDescription>
            {noPayables ? (
              <>
                Đơn <b>{order.code}</b> chưa phát sinh công nợ nào — hoặc chưa nhận hàng, hoặc đã
                thanh toán đủ.
              </>
            ) : (
              <>
                Công nợ chưa trả đủ của đơn <b>{order.code}</b>. Mỗi lần nhận hàng là một dòng; cùng
                số hóa đơn có thể có nhiều dòng.
              </>
            )}
          </DialogDescription>
        </DialogHeader>

        {noPayables ? (
          <PrepayPanel order={order} onCancel={() => onOpenChange(false)} onConfirm={goPrepay} />
        ) : (
          <>
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
                        <TableCell className="text-right text-success tabular-nums">
                          {formatMoney(payable.paid_amount)}
                        </TableCell>
                        <TableCell className="text-right font-semibold text-destructive tabular-nums">
                          {formatMoney(payable.remaining)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}

            {/* CR-260: NCC còn tiền trả trước chưa dùng -> đề nghị cấn trừ NGAY TRÊN
                PHIẾU. Phần cấn trừ chỉ được ghi vào dòng phiếu; kế toán bấm Duyệt
                mới trừ thật vào công nợ — bấm nhầm thì xóa nháp, không phải gỡ gì. */}
            {canOffset && hangingTotal > 0.01 && (
              <div className="space-y-2 rounded-lg border border-warning/40 bg-warning/10 px-4 py-3 text-sm">
                <label className="flex cursor-pointer items-start gap-2">
                  <Checkbox
                    checked={useOffset}
                    onCheckedChange={(checked) => setUseOffset(checked === true)}
                    className="mt-0.5"
                  />
                  <span>
                    Nhà cung cấp đang giữ{' '}
                    <b className="tabular-nums">{formatMoney(hangingTotal)} đ</b> tiền trả trước
                    chưa dùng — <b>ghi phần cấn trừ vào phiếu</b>, người duyệt bấm Duyệt mới trừ
                    thật vào công nợ.
                  </span>
                </label>
                {useOffset && (
                  <dl className="grid gap-1 pl-6 text-sm tabular-nums">
                    <div className="flex justify-between gap-4">
                      <dt className="text-muted-foreground">Nợ đã chọn</dt>
                      <dd>{formatMoney(total)} đ</dd>
                    </div>
                    <div className="flex justify-between gap-4">
                      <dt className="text-muted-foreground">Đề nghị cấn trừ (thực hiện khi duyệt)</dt>
                      <dd>-{formatMoney(effectiveOffset)} đ</dd>
                    </div>
                    <div className="flex justify-between gap-4 border-t pt-1 font-semibold">
                      <dt>Chỉ cần chi thêm</dt>
                      <dd>{formatMoney(payTotal)} đ</dd>
                    </div>
                  </dl>
                )}
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
                Đã chọn {selected.length} khoản ·{' '}
                {effectiveOffset > 0.01 ? (
                  <>
                    Chi thêm: <b className="tabular-nums">{formatMoney(payTotal)} đ</b>{' '}
                    <span className="text-muted-foreground">
                      (đã trừ {formatMoney(effectiveOffset)} đ trả trước)
                    </span>
                  </>
                ) : (
                  <>
                    Tổng đề nghị: <b className="tabular-nums">{formatMoney(total)} đ</b>
                  </>
                )}
              </span>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => onOpenChange(false)}>
                  Đóng
                </Button>
                <Button
                  disabled={!selected.length || createPaymentRequest.isPending}
                  onClick={submit}
                >
                  {createPaymentRequest.isPending ? <Loader2 className="animate-spin" /> : <Receipt />}
                  Tạo yêu cầu thanh toán
                </Button>
              </div>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}

interface PrepayPanelProps {
  order: PurchaseOrderDetail
  onCancel: () => void
  onConfirm: () => void
}

/**
 * Luồng THANH TOÁN TRƯỚC — đơn chưa có công nợ để tick (CR-067).
 *
 * Bản v1 để hẳn nút *Tạo yêu cầu thanh toán* sáng cả khi đơn chưa nợ đồng nào
 * (điều kiện `unpaid_total > 0.01` bị chú thích lại ở `PurchaseOrderDetail.tsx`),
 * vì NCC hay đòi đặt cọc trước khi sản xuất. Bản v2 lúc đầu bê nguyên điều kiện
 * đó nên luồng này mất hẳn — đây là chỗ vá lại.
 */
function PrepayPanel({ order, onCancel, onConfirm }: PrepayPanelProps) {
  const amount = Number(order.order_total) || Number(order.total) || 0

  // CR-268: đơn này đã có phiếu trả trước chưa đối trừ? Có thì cảnh báo để khỏi
  // lập trùng — panel này chỉ dựng khi hộp thoại mở nên query không chạy thừa.
  // Thiếu `payment_request.read` thì tắt hẳn kẻo ăn toast 403 vô ích.
  const { can } = usePermission()
  const { data: hangingData } = usePrepayHanging(
    { supplier_code: order.supplier_code ?? '', po_code: order.code },
    { enabled: can('payment_request', 'read') },
  )
  const hangingTotal = hangingData?.total ?? 0

  return (
    <>
      <div className="space-y-3 rounded-lg border bg-muted/30 px-4 py-3 text-sm">
        <p className="flex items-start gap-2 text-muted-foreground">
          <Info className="mt-0.5 size-4 shrink-0" />
          <span>
            Vẫn lập được phiếu <b>thanh toán trước</b> theo tổng tiền đơn — dùng khi nhà cung cấp
            đòi đặt cọc / trả trước mới sản xuất. Sau khi chi, tiền thành <b>tiền treo</b> của đơn;
            nhận hàng sinh công nợ tới đâu hệ thống <b>tự đối trừ</b> tới đó (CR-268).
          </span>
        </p>

        {hangingTotal > 0.01 && (
          <p className="flex items-start gap-2 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-warning">
            <TriangleAlert className="mt-0.5 size-4 shrink-0" />
            <span>
              Đơn này <b>đã có {formatMoney(hangingTotal)} đ trả trước chưa đối trừ</b> — soát lại
              trước khi lập thêm phiếu mới kẻo chi trùng.
            </span>
          </p>
        )}

        <dl className="grid gap-2 sm:grid-cols-2">
          <div>
            <dt className="text-xs text-muted-foreground">Nhà cung cấp</dt>
            <dd>{order.supplier_name || order.supplier_code || '—'}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground">Số chứng từ tạm (mã MISA)</dt>
            <dd>{order.misa_code || '— (điền tay ở màn sau)'}</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-xs text-muted-foreground">Tổng tiền đơn (theo SL đặt)</dt>
            <dd className="text-base font-semibold text-navy tabular-nums dark:text-foreground">
              {formatMoney(amount)} đ
            </dd>
          </div>
        </dl>
      </div>

      <DialogFooter className="sm:justify-between">
        <span className="text-sm text-muted-foreground">
          Sang màn tạo phiếu để soát lại; rời màn đó sẽ không lưu nháp.
        </span>
        <div className="flex gap-2">
          <Button variant="outline" onClick={onCancel}>
            Đóng
          </Button>
          {/* Tiền 0 đồng thì phiếu vô nghĩa — thường là đơn chưa nhập dòng hàng nào. */}
          <Button disabled={amount <= 0} onClick={onConfirm}>
            <Receipt />
            Lập phiếu thanh toán trước
          </Button>
        </div>
      </DialogFooter>
    </>
  )
}
