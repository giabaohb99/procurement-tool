import { Copy, PauseCircle, Pencil, PlayCircle, Trash2 } from 'lucide-react'
import type { ReactNode } from 'react'

import { ResizableTableHead } from '@/shared/data-table/resizable-table-head'
import { useColumnWidths } from '@/shared/data-table/use-column-widths'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { cn } from '@/shared/utils/cn'
import { formatMoney, formatQuantity } from '@/shared/utils/format-money'
import type { ProductOption } from '../api/purchase-request-support-api'
import { usePurchaseRequestUnits } from '../hooks/use-purchase-request-support'
import { ProgressStatusBadge } from './document-status-badge'
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

const COLUMN_WIDTH_STORAGE_KEY = 'erp.purchase-order.items.column-widths'

/** Bề rộng mặc định + chặn dưới khi kéo giãn của từng cột. */
const COLUMN_SIZES = {
  no: { width: 48, min: 40 },
  code: { width: 200, min: 140 },
  name: { width: 320, min: 200 },
  unit: { width: 110, min: 80 },
  qty: { width: 110, min: 80 },
  price: { width: 140, min: 96 },
  vat: { width: 96, min: 72 },
  amount: { width: 150, min: 110 },
  delivered: { width: 130, min: 100 },
  // Rộng 210: đủ chỗ cho hai nút Tạm ngưng + Hủy đứng CÙNG MỘT HÀNG dưới huy hiệu.
  status: { width: 210, min: 150 },
  action: { width: 120, min: 96 },
} as const

type ColumnKey = keyof typeof COLUMN_SIZES

/** Kẻ ô: viền phải cho mọi ô trừ cột cuối, canh giữa theo chiều dọc. */
const CELL = 'border-r align-middle last:border-r-0'

/**
 * Cột "Thành tiền" tô nền vàng nhạt như bản v1: đây là con số người dùng dò
 * nhiều nhất khi rà đơn, để trắng như mọi cột thì phải đếm cột mới thấy.
 */
const AMOUNT_CELL = 'bg-warning/8'

/**
 * Hai cột đầu GHIM TRÁI: bảng rộng ~1.5 màn hình, cuộn tới cột Trạng thái là
 * mất dấu đang xem dòng nào. Nền phải ĐỤC (`bg-muted` / `bg-card`) vì ô dính
 * nằm đè lên phần bảng đang trôi bên dưới.
 */
const PINNED_KEYS: ColumnKey[] = ['no', 'code']
/**
 * Ô ghim vẽ vạch dọc bằng `inset shadow`, KHÔNG dùng `border-r`: Tailwind
 * preflight đặt `border-collapse: collapse`, ở chế độ đó viền thuộc về bảng nên
 * ô `position: sticky` trôi đi mà bỏ viền lại — cột ghim mất hẳn đường kẻ.
 */
const PINNED_LINE = 'border-r-0 shadow-[inset_-1px_0_0_0_var(--border)]'
const PINNED_HEAD = `sticky z-30 bg-muted ${PINNED_LINE}`
const PINNED_CELL = `sticky z-20 bg-card group-hover:bg-muted ${PINNED_LINE}`

/**
 * Cột Hành động ghim PHẢI: các nút thao tác luôn trong tầm tay dù bảng đang
 * cuộn tới đâu. Vạch ngăn vẽ ở mép TRÁI (`inset 1px 0`), ngược với cột ghim trái.
 */
const PINNED_RIGHT = 'sticky right-0 shadow-[inset_1px_0_0_0_var(--border)]'
const PINNED_RIGHT_HEAD = `${PINNED_RIGHT} z-30 bg-muted`
const PINNED_RIGHT_CELL = `${PINNED_RIGHT} z-20 bg-card group-hover:bg-muted`

/** Tiêu đề các cột, theo đúng thứ tự hiển thị. */
const COLUMNS: { key: ColumnKey; label: ReactNode; className?: string }[] = [
  { key: 'no', label: '#' },
  { key: 'code', label: 'Mã hàng' },
  {
    key: 'name',
    label: (
      <>
        Tên hàng <span className="text-destructive">*</span>
      </>
    ),
  },
  { key: 'unit', label: 'ĐVT' },
  { key: 'qty', label: 'SL đặt', className: 'text-right' },
  { key: 'price', label: 'Đơn giá', className: 'text-right' },
  { key: 'vat', label: 'VAT%', className: 'text-center' },
  { key: 'amount', label: 'Thành tiền', className: cn('text-right', AMOUNT_CELL) },
  { key: 'delivered', label: 'Tiến độ giao', className: 'text-center' },
  { key: 'status', label: 'Trạng thái' },
  { key: 'action', label: 'Hành động', className: 'text-center' },
]

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
}

/**
 * Bảng dòng hàng của ĐMH. Cột tiền hiển thị theo SL ĐẶT (đơn đặt gửi NCC);
 * tiền theo SL THỰC NHẬN nằm ở phần tổng cuối phiếu do backend chốt.
 */
export function PurchaseOrderItemsTable({
  items,
  editable,
  progressEditable,
  onChange,
  onProgressChange,
  onOpenDetail,
}: PurchaseOrderItemsTableProps) {
  const { data: units } = usePurchaseRequestUnits(editable)
  const { widths, resize, totalWidth } = useColumnWidths(COLUMN_WIDTH_STORAGE_KEY, COLUMN_SIZES)

  /** Mốc `left` của cột ghim = tổng bề rộng các cột ghim đứng trước nó. */
  const pinnedOffset = (key: ColumnKey) => {
    const index = PINNED_KEYS.indexOf(key)
    if (index < 0) return undefined
    return PINNED_KEYS.slice(0, index).reduce((sum, pinned) => sum + widths[pinned], 0)
  }

  const patch = (index: number, changes: Partial<PurchaseOrderItem>) =>
    onChange(items.map((item, current) => (current === index ? { ...item, ...changes } : item)))

  // Không đụng `invoice_name`: danh mục sản phẩm ở API này không trả tên hóa
  // đơn, backend tự suy theo `product_code` khi dòng để trống.
  const applyProduct = (index: number, product: ProductOption | null) =>
    patch(index, {
      product_code: product?.code ?? '',
      product_name: product?.name ?? '',
      unit: product?.unit ?? '',
      item_group: product?.item_group ?? '',
    })

  return (
    // `isolate`: cột ghim dùng `z-30`, thiếu ngữ cảnh xếp lớp riêng thì nó trồi
    // lên trên cả thanh tiêu đề của trang khi cuộn.
    <div className="isolate overflow-x-auto rounded-lg border">
      {/*
        `table-fixed` + bề rộng cứng: để bảng tự chia (auto) thì cột Tên hàng
        nuốt hết chỗ, ô nhập SL/Đơn giá còn ~50px và số bị cắt cụt. Bảng rộng
        hơn khung là cố ý — cuộn ngang dễ chịu hơn là đọc số bị xén.
      */}
      <Table className="table-fixed" style={{ width: totalWidth }}>
        <TableHeader className="bg-muted">
          <TableRow>
            {COLUMNS.map((column) => (
              <ResizableTableHead
                key={column.key}
                width={widths[column.key]}
                minWidth={COLUMN_SIZES[column.key].min}
                left={pinnedOffset(column.key)}
                className={cn(
                  CELL,
                  column.className,
                  PINNED_KEYS.includes(column.key) && PINNED_HEAD,
                  column.key === 'action' && PINNED_RIGHT_HEAD,
                )}
                onResize={(width) => resize(column.key, width)}
              >
                {column.label}
              </ResizableTableHead>
            ))}
          </TableRow>
        </TableHeader>

        <TableBody>
          {items.length === 0 && (
            <TableRow>
              <TableCell colSpan={11} className="h-20 text-center text-muted-foreground">
                Chưa có dòng hàng nào.
              </TableCell>
            </TableRow>
          )}

          {items.map((item, index) => {
            const locked = isLineLocked(item)
            const received = isLineReceived(item)
            const cellEditable = editable && !locked

            return (
              // `group`: ô ghim tự tô lại nền khi rê chuột — nền đục không ăn
              // theo `hover` của hàng như ô thường.
              <TableRow key={item.id ?? `new-${index}`} className="group">
                <TableCell
                  className={cn(CELL, PINNED_CELL, 'text-muted-foreground')}
                  style={{ left: pinnedOffset('no') }}
                >
                  {index + 1}
                </TableCell>

                <TableCell
                  className={cn(CELL, PINNED_CELL)}
                  style={{ left: pinnedOffset('code') }}
                  title={received ? PRODUCT_LOCK_HINT : undefined}
                >
                  {cellEditable && !received ? (
                    <PurchaseRequestProductPicker
                      code={item.product_code}
                      name={item.product_name}
                      onPick={(product) => applyProduct(index, product)}
                    />
                  ) : (
                    <span className="font-medium">{item.product_code || '—'}</span>
                  )}
                </TableCell>

                <TableCell className={cn(CELL, 'whitespace-normal')}>
                  {cellEditable && !received ? (
                    <Input
                      value={item.product_name}
                      placeholder="Tên hàng"
                      onChange={(event) => patch(index, { product_name: event.target.value })}
                    />
                  ) : (
                    <span className="whitespace-pre-wrap">{item.product_name || '—'}</span>
                  )}
                </TableCell>

                <TableCell className={CELL}>
                  {cellEditable && !received ? (
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
                  )}
                </TableCell>

                <TableCell className={cn(CELL, 'text-right')}>
                  <NumberCell
                    value={item.qty_order}
                    editable={cellEditable}
                    onChange={(value) => patch(index, { qty_order: value })}
                    format={formatQuantity}
                  />
                </TableCell>

                <TableCell className={cn(CELL, 'text-right')}>
                  <NumberCell
                    value={item.price}
                    editable={cellEditable}
                    onChange={(value) => patch(index, { price: value })}
                    format={formatMoney}
                  />
                </TableCell>

                <TableCell className={cn(CELL, 'text-center')}>
                  {cellEditable ? (
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
                  )}
                </TableCell>

                <TableCell
                  className={cn(CELL, AMOUNT_CELL, 'text-right font-semibold tabular-nums')}
                >
                  {formatMoney(orderLineAmount(item))} đ
                </TableCell>

                <TableCell className={cn(CELL, 'text-center text-xs text-muted-foreground')}>
                  {/* Huy hiệu XUỐNG DÒNG: để cùng hàng với con số thì cột phải
                      rộng gấp đôi mới không bị ngắt chữ giữa chừng. */}
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
                </TableCell>

                <TableCell className={cn(CELL, 'text-center')}>
                  {/* Nút đổi tiến độ nằm NGAY DƯỚI huy hiệu trạng thái (giống
                      v1): chúng thao tác lên chính trạng thái này, để lẫn ở cột
                      Hành động thì người dùng phải dò xem nút tác động vào đâu. */}
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
                  {/* Chỉ hiện lý do ở hai trạng thái do người dùng đặt tay; kèm
                      nhãn "Lý do" để khỏi trôi nổi như một con số vô nghĩa. */}
                  {item.pause_reason &&
                    ['Tạm ngưng', 'Hủy đơn'].includes(item.progress_status ?? '') && (
                      <p className="mt-1 text-xs text-muted-foreground">
                        Lý do: {item.pause_reason}
                      </p>
                    )}
                </TableCell>

                <TableCell className={cn(CELL, PINNED_RIGHT_CELL, 'text-center')}>
                  <LineActions
                    editable={editable}
                    locked={locked}
                    onOpenDetail={onOpenDetail ? () => onOpenDetail(index) : undefined}
                    onDuplicate={() =>
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
                    }
                    onRemove={() => onChange(items.filter((_, current) => current !== index))}
                  />
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
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
      // Ẩn nút tăng/giảm: chúng ăn mất ~20px của ô vốn đã hẹp, che luôn số.
      className="w-full px-2 text-right tabular-nums [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
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
            className="text-destructive"
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
