import { Loader2 } from 'lucide-react'
import { useMemo, useRef, useState } from 'react'

import { useIsMobile } from '@/shared/hooks/use-mobile'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Label } from '@/shared/ui/label'
import { NumberInput, PRICE_MAX_DECIMALS } from '@/shared/ui/number-input'
import { RequiredMark } from '@/shared/ui/required-mark'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/ui/table'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'
import {
  formatMoneyWithCurrency,
  formatQuantity,
  formatUnitPriceWithCurrency,
} from '@/shared/utils/format-money'
import { useAdjustPurchaseOrderPrices } from '../hooks/use-purchase-order'
import type { PurchaseOrderDetail } from '../types/purchase-order-detail'
import { resolveLineCurrency } from '../utils/purchase-order-import-cost'
import {
  buildPriceAdjustPayload,
  draftPriceOf,
  isPriceChanged,
  isPriceValid,
  listPriceAdjustableLines,
  receivedAmountDelta,
  type PriceAdjustDraft,
  type PriceAdjustLine,
} from '../utils/purchase-order-price-adjust'

interface PurchaseOrderPriceAdjustDialogProps {
  /** Bản đơn ĐÃ LƯU trên máy chủ — giá hiện tại và id dòng lấy từ đây. */
  order: PurchaseOrderDetail
  onClose: () => void
}

/** Một dòng của hộp, đã tính sẵn mọi thứ để bảng (khổ rộng) và thẻ (khổ hẹp) vẽ cùng một số. */
interface PriceAdjustRow {
  line: PriceAdjustLine
  /** Số thứ tự của dòng TRÊN ĐƠN (không phải trong hộp) — đơn có thể có nhiều dòng trùng mã. */
  lineNumber: number
  currency: string
  newPrice: number
  changed: boolean
  valid: boolean
  /** `null` = dòng chưa nhận hàng. */
  delta: number | null
}

const NOT_RECEIVED_HINT = 'Dòng chưa nhận hàng — chưa có tiền hàng nào để chênh.'
const INVALID_PRICE_MESSAGE = 'Đơn giá mới phải lớn hơn 0.'

/** Chênh lệch có dấu: tăng mang dấu cộng, giảm mang dấu trừ, không đổi thì là 0. */
function formatDelta(delta: number, currency: string): string {
  if (Math.abs(delta) < 0.005) return formatMoneyWithCurrency(0, currency)
  return `${delta > 0 ? '+' : '−'}${formatMoneyWithCurrency(Math.abs(delta), currency)}`
}

/**
 * Hộp SỬA GIÁ SAU DUYỆT của Đơn mua hàng (bao-CR-794).
 *
 * Đơn đã duyệt khóa đơn giá; trước đây muốn sửa phải Hủy duyệt, mà Hủy duyệt bị chặn khi đơn đã
 * nhận hàng. Hộp này cho người có quyền duyệt sửa thẳng đơn giá từng dòng — đơn giữ nguyên trạng
 * thái. Chỉ liệt kê dòng chưa Hoàn thành / Hủy, và chỉ gửi lên những dòng ĐỔI giá.
 *
 * Trang dựng hộp khi mở và gỡ khi đóng, nên mỗi lần mở là một bảng giá sạch.
 */
export function PurchaseOrderPriceAdjustDialog({
  order,
  onClose,
}: PurchaseOrderPriceAdjustDialogProps) {
  const [draft, setDraft] = useState<PriceAdjustDraft>({})
  const [reason, setReason] = useState('')
  const adjustPrices = useAdjustPurchaseOrderPrices(order.id)
  const isMobile = useIsMobile()
  /** Chặn bấm đúp ngay trong tick — `disabled` chỉ có hiệu lực ở lượt vẽ sau. */
  const submittingRef = useRef(false)

  const lines = useMemo(() => listPriceAdjustableLines(order.items), [order.items])
  const rows: PriceAdjustRow[] = lines.map((line) => ({
    line,
    lineNumber: order.items.indexOf(line) + 1,
    currency: resolveLineCurrency(line, order).currency,
    newPrice: draftPriceOf(line, draft),
    changed: isPriceChanged(line, draft),
    valid: isPriceValid(line, draft),
    delta: receivedAmountDelta(line, draft),
  }))

  const payload = buildPriceAdjustPayload(lines, draft, reason)
  const changedRows = rows.filter((row) => row.changed)
  const hasInvalidPrice = rows.some((row) => !row.valid)

  //  Tổng chênh lệch chỉ cộng được khi các dòng đổi giá đã nhận hàng cùng MỘT loại tiền.
  const deltaRows = changedRows.filter((row) => row.valid && row.delta !== null)
  const deltaCurrencies = new Set(deltaRows.map((row) => row.currency))
  const totalDelta =
    deltaCurrencies.size === 1 ? deltaRows.reduce((sum, row) => sum + (row.delta ?? 0), 0) : null

  function setPrice(lineId: number, price: number) {
    setDraft((current) => ({ ...current, [lineId]: price }))
  }

  async function handleSubmit() {
    if (!payload || submittingRef.current) return
    submittingRef.current = true
    try {
      await adjustPrices.mutateAsync(payload)
      onClose()
    } catch {
      //  Câu lỗi của máy chủ đã được tầng gọi API bật lên — giữ hộp mở để người dùng xử lý tiếp.
    } finally {
      submittingRef.current = false
    }
  }

  function renderPriceInput(row: PriceAdjustRow) {
    return (
      <div className="space-y-1">
        <NumberInput
          aria-label={`Đơn giá mới dòng ${row.lineNumber}`}
          value={row.newPrice}
          maxDecimals={PRICE_MAX_DECIMALS}
          disabled={adjustPrices.isPending}
          className={cn(
            'h-8 text-right',
            !row.valid && 'border-destructive focus-visible:ring-destructive/30',
          )}
          onChange={(price) => setPrice(row.line.id, price)}
        />
        {!row.valid && <p className="text-xs text-destructive">{INVALID_PRICE_MESSAGE}</p>}
      </div>
    )
  }

  function renderDelta(row: PriceAdjustRow) {
    if (row.delta === null) {
      return (
        <span className="text-muted-foreground" title={NOT_RECEIVED_HINT}>
          —
        </span>
      )
    }
    if (!row.valid) return <span className="text-muted-foreground">—</span>
    return (
      <span
        className={cn(
          'tabular-nums',
          !row.changed && 'text-muted-foreground',
          row.changed && row.delta > 0 && 'font-medium text-warning',
          row.changed && row.delta < 0 && 'font-medium text-success',
        )}
      >
        {formatDelta(row.delta, row.currency)}
      </span>
    )
  }

  return (
    <Dialog open onOpenChange={(open) => !open && !adjustPrices.isPending && onClose()}>
      <DialogContent className="sm:max-w-5xl">
        <DialogHeader>
          <DialogTitle>Sửa giá sau duyệt{order.code ? ` — ${order.code}` : ''}</DialogTitle>
          <DialogDescription>
            Đơn giữ nguyên trạng thái. Công nợ, lịch sử mua hàng và sổ giá tính lại theo giá mới. Đơn
            đã có yêu cầu thanh toán gửi duyệt thì không sửa giá được.
          </DialogDescription>
        </DialogHeader>

        {rows.length === 0 ? (
          <p className="rounded-md border border-dashed px-3 py-6 text-center text-sm text-muted-foreground">
            Đơn không còn dòng nào sửa giá được — mọi dòng đã Hoàn thành hoặc đã Hủy.
          </p>
        ) : isMobile ? (
          <ul className="space-y-2">
            {rows.map((row) => (
              <li
                key={row.line.id}
                className={cn(
                  'space-y-2 rounded-md border px-3 py-2 text-sm',
                  row.changed && 'border-warning/40 bg-warning/10',
                )}
              >
                <div>
                  <p className="font-medium">
                    {row.lineNumber}. {row.line.product_code || '—'}
                  </p>
                  <p className="text-xs text-muted-foreground">{row.line.product_name}</p>
                </div>
                <p className="text-xs text-muted-foreground">
                  SL đặt {formatQuantity(row.line.qty_order) || '0'} · Đã nhận{' '}
                  {formatQuantity(row.line.qty_received ?? 0) || '0'} {row.line.unit}
                </p>
                <p className="flex justify-between gap-3">
                  <span className="text-muted-foreground">Đơn giá hiện tại</span>
                  <span className="tabular-nums">
                    {formatUnitPriceWithCurrency(row.line.price, row.currency) || '0'}
                  </span>
                </p>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Đơn giá mới</p>
                  {renderPriceInput(row)}
                </div>
                <p className="flex justify-between gap-3">
                  <span className="text-muted-foreground">Chênh lệch đã nhận (chưa VAT)</span>
                  {renderDelta(row)}
                </p>
              </li>
            ))}
          </ul>
        ) : (
          <Table containerClassName="rounded-md border">
            <TableHeader>
              <TableRow>
                <TableHead className="w-10 text-right">#</TableHead>
                <TableHead>Mã hàng</TableHead>
                <TableHead>Tên hàng</TableHead>
                <TableHead className="text-right">SL đặt</TableHead>
                <TableHead className="text-right">SL đã nhận</TableHead>
                <TableHead className="text-right">Đơn giá hiện tại</TableHead>
                <TableHead className="w-40 text-right">Đơn giá mới</TableHead>
                <TableHead
                  className="text-right"
                  title="SL đã nhận × (đơn giá mới − đơn giá hiện tại), chưa VAT"
                >
                  Chênh lệch đã nhận (chưa VAT)
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row) => (
                <TableRow
                  key={row.line.id}
                  className={cn(row.changed && 'bg-warning/10 hover:bg-warning/15')}
                >
                  <TableCell className="text-right text-muted-foreground tabular-nums">
                    {row.lineNumber}
                  </TableCell>
                  <TableCell className="font-medium whitespace-nowrap">
                    {row.line.product_code || '—'}
                  </TableCell>
                  <TableCell className="min-w-40 whitespace-normal">
                    {row.line.product_name}
                  </TableCell>
                  <TableCell className="text-right whitespace-nowrap tabular-nums">
                    {formatQuantity(row.line.qty_order) || '0'}
                    {row.line.unit && (
                      <span className="ml-1 text-xs text-muted-foreground">{row.line.unit}</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatQuantity(row.line.qty_received ?? 0) || '0'}
                  </TableCell>
                  <TableCell className="text-right whitespace-nowrap tabular-nums">
                    {formatUnitPriceWithCurrency(row.line.price, row.currency) || '0'}
                  </TableCell>
                  <TableCell className="align-top">{renderPriceInput(row)}</TableCell>
                  <TableCell className="text-right whitespace-nowrap">{renderDelta(row)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}

        {changedRows.length > 0 && (
          <p className="text-sm text-muted-foreground">
            Đang đổi giá <b className="text-foreground">{changedRows.length}</b> dòng.
            {totalDelta !== null && deltaRows.length > 0 && (
              <>
                {' '}
                Tiền hàng đã nhận (chưa VAT) thay đổi{' '}
                <b className="text-foreground tabular-nums">
                  {formatDelta(totalDelta, deltaRows[0].currency)}
                </b>
                .
              </>
            )}
          </p>
        )}

        <div className="space-y-1.5">
          <Label htmlFor="po-price-adjust-reason">
            Lý do sửa giá
            <RequiredMark />
          </Label>
          <Textarea
            id="po-price-adjust-reason"
            rows={3}
            value={reason}
            placeholder="Ví dụ: nhà cung cấp báo lại giá sau khi hàng về"
            disabled={adjustPrices.isPending}
            onChange={(event) => setReason(event.target.value)}
          />
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            disabled={adjustPrices.isPending}
            onClick={onClose}
          >
            Hủy
          </Button>
          <Button
            type="button"
            disabled={!payload || adjustPrices.isPending}
            title={
              hasInvalidPrice
                ? INVALID_PRICE_MESSAGE
                : changedRows.length === 0
                  ? 'Chưa có dòng nào đổi giá.'
                  : !reason.trim()
                    ? 'Nhập lý do sửa giá.'
                    : undefined
            }
            onClick={() => void handleSubmit()}
          >
            {adjustPrices.isPending && <Loader2 className="animate-spin" />}
            Lưu giá mới
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
