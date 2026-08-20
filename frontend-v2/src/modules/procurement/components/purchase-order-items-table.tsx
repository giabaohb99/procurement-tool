import { useMemo, useState } from 'react'
import { Copy, History, PauseCircle, Pencil, PlayCircle, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import { LinesTable } from '@/shared/data-table/lines-table'
import type { LinesTableColumn } from '@/shared/data-table/types'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { CopyButton } from '@/shared/ui/copy-button'
import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { formatMoney, formatQuantity } from '@/shared/utils/format-money'
import type {
  ProductOption,
  PurchaseHistoryRow,
} from '../api/purchase-request-support-api'
import { usePurchaseRequestUnits } from '../hooks/use-purchase-request-support'
import { ProgressStatusBadge } from './document-status-badge'
import { PurchaseHistoryDialog } from './purchase-history-dialog'
import { PurchaseRequestProductPicker } from './purchase-request-product-picker'
import {
  isLineLocked,
  isLineReceived,
  PO_VAT_OPTIONS,
  PRODUCT_LOCK_HINT,
  type PurchaseOrderItem,
} from '../types/purchase-order-detail'

/** Thành tiền theo SL ĐẶT — hiện ngay khi gõ, không chờ backend tính lại. */
export function orderLineAmount(item: PurchaseOrderItem): number {
  return (item.qty_order || 0) * (item.price || 0) * (1 + (item.vat || 0) / 100)
}

const TABLE_STORAGE_KEY = 'purchase-order-items'

/** Lịch sử có ghi thì lấy, không thì giữ nguyên thứ đang có trên dòng. */
function preferHistory(previous: string, historyValue?: string): string {
  return (historyValue ?? '').trim() || previous || ''
}

interface PurchaseOrderItemsTableProps {
  items: PurchaseOrderItem[]
  /** Sửa được nội dung dòng (đơn chưa chốt + có quyền ghi). */
  editable: boolean
  /** Cập nhật tiến độ dòng (đơn đã duyệt trở đi). */
  progressEditable: boolean
  onChange: (items: PurchaseOrderItem[]) => void
  /** Đổi tiến độ dòng — trang gọi endpoint riêng và hỏi lý do khi cần. */
  onProgressChange?: (item: PurchaseOrderItem, status: string) => void
  /** Mở hộp chi tiết dòng (thông tin đầy đủ + các lần giao). */
  onOpenDetail?: (index: number) => void
  /**
   * Xóa / nhân bản dòng làm lệch chỉ số của mọi dòng phía sau. Trang đang giữ hộ
   * phiếu giao của lần giao chưa lưu theo chỉ số nên phải biết chỗ vừa đổi.
   */
  onLineRemoved?: (index: number) => void
  onLineDuplicated?: (index: number) => void
}

/**
 * Bảng dòng hàng của ĐMH hỗ trợ:
 * - Ghim cột cố định (default: No, Code, Name).
 * - Kéo thả trực tiếp tiêu đề cột trên bảng để đổi thứ tự.
 * - Chế độ Bảng rút gọn vs Bảng đầy đủ.
 * - Kéo giãn / co nhỏ độ rộng cột & nhớ tự động vào localStorage.
 */
export function PurchaseOrderItemsTable({
  items,
  editable,
  progressEditable,
  onChange,
  onProgressChange,
  onOpenDetail,
  onLineRemoved,
  onLineDuplicated,
}: PurchaseOrderItemsTableProps) {
  const { data: units } = usePurchaseRequestUnits(editable)
  /** Dòng đang xem lịch sử mua hàng; `null` = hộp thoại đang đóng. */
  const [historyIndex, setHistoryIndex] = useState<number | null>(null)

  const columns = useMemo<LinesTableColumn[]>(() => [
    {
      key: 'no',
      header: '#',
      width: 48,
      minWidth: 40,
      hideable: false,
      defaultPinned: true,
      align: 'center',
    },
    {
      key: 'code',
      header: 'Mã hàng',
      // Rộng hơn bề ngang của mã: ô còn chứa nút chép mã và nút lịch sử mua hàng.
      width: 212,
      minWidth: 100,
      hideable: false,
      defaultPinned: true,
    },
    {
      key: 'name',
      header: 'Tên hàng *',
      width: 300,
      minWidth: 140,
      hideable: false,
      defaultPinned: true,
    },
    { key: 'unit', header: 'ĐVT', width: 90, minWidth: 50 },
    { key: 'qty', header: 'SL đặt', width: 100, minWidth: 60, align: 'right' },
    { key: 'price', header: 'Đơn giá', width: 130, minWidth: 70, align: 'right' },
    {
      key: 'vat',
      header: 'VAT%',
      width: 80,
      minWidth: 50,
      align: 'center',
      compactHidden: true,
    },
    { key: 'amount', header: 'Thành tiền', width: 140, minWidth: 80, align: 'right' },
    {
      key: 'delivered',
      header: 'Tiến độ giao',
      width: 120,
      minWidth: 70,
      align: 'center',
      compactHidden: true,
    },
    {
      key: 'status',
      header: 'Trạng thái',
      width: 200,
      minWidth: 130,
      align: 'center',
      compactHidden: true,
    },
    {
      key: 'action',
      header: 'Hành động',
      width: 96,
      minWidth: 60,
      hideable: false,
      align: 'center',
    },
  ], [])

  const patch = (index: number, changes: Partial<PurchaseOrderItem>) =>
    onChange(items.map((item, current) => (current === index ? { ...item, ...changes } : item)))

  const applyProduct = (index: number, product: ProductOption | null) =>
    patch(index, {
      product_code: product?.code ?? '',
      product_name: product?.name ?? '',
      unit: product?.unit ?? '',
      item_group: product?.item_group ?? '',
    })

  /**
   * Điền một lần mua cũ vào dòng đang chọn.
   *
   * ĐVT / SL / đơn giá / VAT thì đè thẳng — đó chính là thứ người dùng mở lịch sử
   * ra để lấy. Mấy ô mô tả (tên hóa đơn, quy cách, mã thành phẩm, kho nhận, ghi
   * chú) chỉ điền khi lần mua cũ có ghi: đơn cũ bỏ trống mà vẫn đè thì hóa ra xóa
   * mất thứ người dùng vừa gõ tay.
   */
  function applyPurchaseHistory(index: number, history: PurchaseHistoryRow) {
    const current = items[index]
    if (!current) return

    const vat = Number(history.vat)
    patch(index, {
      unit: history.unit || current.unit,
      qty_order: Number(history.qty_order) || 0,
      price: Number(history.price) || 0,
      // VAT ngoài danh sách chọn thì giữ mức cũ, không thì ô VAT hiện trống trơn.
      vat: PO_VAT_OPTIONS.some((option) => option === vat) ? vat : current.vat,
      invoice_name: preferHistory(current.invoice_name, history.extra?.invoice_name),
      item_group: preferHistory(current.item_group, history.extra?.item_group),
      spec: preferHistory(current.spec, history.extra?.spec),
      fg_code: preferHistory(current.fg_code, history.extra?.fg_code),
      fg_name: preferHistory(current.fg_name, history.extra?.fg_name),
      warehouse_code: preferHistory(current.warehouse_code, history.extra?.warehouse_code),
      note: preferHistory(current.note, history.extra?.item_note),
    })
    toast.success('Đã điền giá và thông tin dòng từ lịch sử — bấm Lưu để ghi nhận')
  }

  function renderCell(key: string, item: PurchaseOrderItem, index: number) {
    const locked = isLineLocked(item)
    const received = isLineReceived(item)
    const cellEditable = editable && !locked

    switch (key) {
      case 'no':
        return <span className="text-muted-foreground">{index + 1}</span>

      case 'code':
        return (
          <div className="flex min-w-0 items-center gap-0.5">
            <div className="min-w-0 flex-1">
              {cellEditable && !received ? (
                <PurchaseRequestProductPicker
                  code={item.product_code}
                  name={item.product_name}
                  onPick={(product) => applyProduct(index, product)}
                />
              ) : (
                <span className="block break-words whitespace-normal leading-snug font-medium" title={received ? PRODUCT_LOCK_HINT : undefined}>
                  {item.product_code || '—'}
                </span>
              )}
            </div>
            {/* Đơn còn sửa được thì mã nằm trong ô chọn (một <button>): bôi đen
                không được, nên phải có nút chép mới lấy mã ra ngoài được. */}
            <CopyButton value={item.product_code} label="mã hàng" className="size-7" />
            {/*
              KHÔNG ẩn theo quyền sửa: đơn đang chờ duyệt (bị khóa sửa) chính là
              lúc người duyệt cần đối chiếu giá cũ nhất. Dòng khóa thì hộp thoại
              mở ở chế độ chỉ xem, bỏ đường điền giá.
            */}
            {!!item.product_code && (
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                className="size-7 shrink-0 text-muted-foreground"
                title="Xem lịch sử mua hàng gần nhất"
                aria-label={`Xem lịch sử mua hàng của ${item.product_code}`}
                onClick={() => setHistoryIndex(index)}
              >
                <History />
              </Button>
            )}
          </div>
        )

      case 'name':
        return cellEditable && !received ? (
          <Input
            value={item.product_name}
            placeholder="Tên hàng"
            onChange={(event) => patch(index, { product_name: event.target.value })}
          />
        ) : (
          <span className="block break-words whitespace-normal leading-snug">
            {item.product_name || '—'}
          </span>
        )

      case 'unit':
        return cellEditable && !received ? (
          <Select
            value={item.unit || undefined}
            onValueChange={(value) => patch(index, { unit: value })}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="—" />
            </SelectTrigger>
            <SelectContent>
              {(units?.items ?? []).map((unit) => (
                <SelectItem key={unit.id} value={unit.name}>
                  {unit.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : (
          item.unit || '—'
        )

      case 'qty':
        return (
          <NumberCell
            value={item.qty_order}
            editable={cellEditable}
            onChange={(value) => patch(index, { qty_order: value })}
            format={formatQuantity}
          />
        )

      case 'price':
        return (
          <NumberCell
            value={item.price}
            editable={cellEditable}
            onChange={(value) => patch(index, { price: value })}
            format={formatMoney}
          />
        )

      case 'vat':
        return cellEditable ? (
          <Select
            value={String(item.vat ?? 0)}
            onValueChange={(value) => patch(index, { vat: Number(value) })}
          >
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PO_VAT_OPTIONS.map((option) => (
                <SelectItem key={option} value={String(option)}>
                  {option}%
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : (
          `${item.vat ?? 0}%`
        )

      case 'amount':
        return (
          <span className="tabular-nums font-semibold text-navy">
            {formatMoney(orderLineAmount(item))} đ
          </span>
        )

      case 'delivered':
        return (
          <div className="text-center text-xs text-muted-foreground">
            <span className="block tabular-nums">
              {formatQuantity(item.qty_received ?? 0)}/{formatQuantity(item.qty_order)}
            </span>
            {item.is_short_delivery && (
              <Badge
                variant="secondary"
                className="mt-1 border-0 bg-warning/10 text-warning"
                title="Tổng SL đã nhận nhỏ hơn SL đặt"
              >
                Giao thiếu
              </Badge>
            )}
          </div>
        )

      case 'status':
        return (
          <div className="text-center">
            <ProgressStatusBadge status={item.progress_status ?? 'Chưa đặt hàng'} />
            {progressEditable && !!item.id && !locked && (
              <div className="mt-1 flex flex-wrap items-center justify-center gap-1">
                {item.progress_status === 'Tạm ngưng' ? (
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-7 px-2 text-xs"
                    onClick={() => onProgressChange?.(item, '__resume__')}
                  >
                    <PlayCircle />
                    Tiếp tục
                  </Button>
                ) : (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-7 px-2 text-xs"
                      onClick={() => onProgressChange?.(item, 'Tạm ngưng')}
                    >
                      <PauseCircle />
                      Tạm ngưng
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-7 px-2 text-xs text-destructive hover:text-destructive"
                      onClick={() => onProgressChange?.(item, 'Hủy đơn')}
                    >
                      Hủy
                    </Button>
                  </>
                )}
              </div>
            )}
            {item.pause_reason &&
              ['Tạm ngưng', 'Hủy đơn'].includes(item.progress_status ?? '') && (
                <p className="mt-1 text-xs text-muted-foreground">
                  Lý do: {item.pause_reason}
                </p>
              )}
          </div>
        )

      case 'action':
        return (
          <LineActions
            editable={editable}
            locked={locked}
            onOpenDetail={onOpenDetail ? () => onOpenDetail(index) : undefined}
            onDuplicate={() => {
              onChange([
                ...items.slice(0, index + 1),
                {
                  ...item,
                  id: undefined,
                  deliveries: [],
                  qty_received: 0,
                  qty_remaining: 0,
                  progress_status: 'Chưa đặt hàng',
                  pause_reason: '',
                  status_before_pause: '',
                },
                ...items.slice(index + 1),
              ])
              onLineDuplicated?.(index)
            }}
            onRemove={() => {
              onChange(items.filter((_, current) => current !== index))
              onLineRemoved?.(index)
            }}
          />
        )

      default:
        return null
    }
  }

  const historyItem = historyIndex === null ? null : items[historyIndex]

  return (
    <>
      <LinesTable
        columns={columns}
        rows={items}
        storageKey={TABLE_STORAGE_KEY}
        rowKey={(item, index) => item.id ?? `new-${index}`}
        renderCell={renderCell}
        title={`Danh sách dòng hàng (${items.length} dòng)`}
        emptyMessage="Chưa có dòng hàng nào."
        cellClassName={(key) => (key === 'amount' ? 'bg-warning/8' : undefined)}
      />

      <PurchaseHistoryDialog
        open={historyIndex !== null}
        productCode={historyItem?.product_code ?? ''}
        productName={historyItem?.product_name ?? ''}
        // Dòng đã nhận hàng cũng chỉ xem: kho đã ghi theo mã cũ nên backend chặn
        // đổi nhận diện sản phẩm, điền vào chỉ tổ lưu lên rồi báo lỗi.
        readOnly={
          !historyItem ||
          !editable ||
          isLineLocked(historyItem) ||
          isLineReceived(historyItem)
        }
        onOpenChange={(open) => {
          if (!open) setHistoryIndex(null)
        }}
        onPick={(history) => {
          if (historyIndex !== null) applyPurchaseHistory(historyIndex, history)
        }}
      />
    </>
  )
}

/** Ô số: gõ tự do khi sửa, còn lại hiện đã định dạng theo chuẩn tiền/số lượng. */
function NumberCell({
  value,
  editable,
  onChange,
  format,
}: {
  value: number
  editable: boolean
  onChange: (value: number) => void
  format: (value: number) => string
}) {
  if (!editable) return <span className="tabular-nums">{format(value || 0)}</span>

  return (
    <Input
      type="number"
      className="w-full px-2 text-right tabular-nums"
      value={value ?? 0}
      onChange={(event) => onChange(Number(event.target.value) || 0)}
    />
  )
}

/** Mở chi tiết, nhân bản và xóa dòng. Tiến độ dòng nằm ở cột Trạng thái. */
function LineActions({
  editable,
  locked,
  onOpenDetail,
  onDuplicate,
  onRemove,
}: {
  editable: boolean
  locked: boolean
  onOpenDetail?: () => void
  onDuplicate: () => void
  onRemove: () => void
}) {
  return (
    <div className="flex items-center justify-center gap-1">
      {onOpenDetail && (
        <Button
          variant="ghost"
          size="icon-sm"
          title="Chi tiết dòng & các lần giao hàng"
          onClick={onOpenDetail}
        >
          <Pencil />
        </Button>
      )}

      {editable && !locked && (
        <>
          <Button variant="ghost" size="icon-sm" title="Nhân bản dòng" onClick={onDuplicate}>
            <Copy />
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            className="text-destructive hover:text-destructive"
            title="Xóa dòng"
            onClick={onRemove}
          >
            <Trash2 />
          </Button>
        </>
      )}
    </div>
  )
}
