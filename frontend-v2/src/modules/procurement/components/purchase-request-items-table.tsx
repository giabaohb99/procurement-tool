import { useState, type CSSProperties, type ReactNode } from 'react'
import { History, Pencil, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import { ColumnResizeHandle } from '@/shared/data-table/column-resize-handle'
import { Button } from '@/shared/ui/button'
import { DatePicker } from '@/shared/ui/date-picker'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
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
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import {
  formatMoney,
  formatQuantity,
  formatUnitPrice,
} from '@/shared/utils/format-money'
import type {
  ProductOption,
  PurchaseHistoryRow,
} from '../api/purchase-request-support-api'
import {
  usePurchaseRequestItemGroups,
  usePurchaseRequestUnits,
  usePurchaseRequestWarehouses,
} from '../hooks/use-purchase-request-support'
import {
  VAT_OPTIONS,
  type PurchaseRequestItem,
} from '../types/purchase-request-detail'
import { ProgressStatusBadge } from './document-status-badge'
import { PurchaseRequestHistoryDialog } from './purchase-request-history-dialog'
import { PurchaseRequestProductPicker } from './purchase-request-product-picker'

/**
 * Bảng dòng hàng có nhiều cột nghiệp vụ nên ba cột nhận diện được ghim cứng
 * bên trái. Người dùng kéo mép tiêu đề để đổi độ rộng; cấu hình được nhớ riêng
 * cho màn YCMH nhưng không đưa vào menu Cột.
 */
const PINNED = {
  noHead: 'sticky z-40 bg-muted',
  noCell: 'sticky z-20 bg-card group-hover:bg-muted',
  codeHead: 'sticky z-40 bg-muted',
  codeCell: 'sticky z-20 bg-card group-hover:bg-muted',
  nameHead:
    'sticky z-40 bg-muted shadow-[inset_-2px_0_0_0_var(--border)]',
  nameCell:
    'sticky z-20 bg-card group-hover:bg-muted shadow-[inset_-2px_0_0_0_var(--border)]',
  actionHead:
    'sticky right-0 z-40 border-l bg-muted [background-clip:padding-box]',
  actionCell:
    'sticky right-0 z-20 border-l bg-card [background-clip:padding-box] group-hover:bg-muted',
} as const

const COLUMN_WIDTH_STORAGE_KEY = 'erp.purchase-request.items.column-widths'

/** Mã giả cho mục "bỏ chọn NSTM" — xem chú thích ở ô chọn NSTM. */
const UNASSIGNED = '__unassigned__'

const COLUMN_SIZES = {
  no: { width: 48, min: 48 },
  code: { width: 150, min: 120 },
  name: { width: 360, min: 220 },
  warehouse: { width: 240, min: 140 },
  group: { width: 160, min: 120 },
  unit: { width: 80, min: 64 },
  qty: { width: 80, min: 64 },
  price: { width: 112, min: 88 },
  vat: { width: 64, min: 56 },
  amount: { width: 128, min: 104 },
  status: { width: 144, min: 112 },
  progress: { width: 112, min: 88 },
  expected: { width: 128, min: 104 },
  assignee: { width: 160, min: 120 },
  action: { width: 80, min: 72 },
} as const

type ColumnKey = keyof typeof COLUMN_SIZES
type ColumnWidths = Record<ColumnKey, number>

const DEFAULT_COLUMN_WIDTHS = Object.fromEntries(
  Object.entries(COLUMN_SIZES).map(([key, value]) => [key, value.width]),
) as ColumnWidths

function readColumnWidths(): ColumnWidths {
  try {
    const saved = JSON.parse(localStorage.getItem(COLUMN_WIDTH_STORAGE_KEY) || '{}') as Record<
      string,
      unknown
    >
    return Object.fromEntries(
      Object.entries(COLUMN_SIZES).map(([key, size]) => {
        const value = saved[key]
        return [
          key,
          typeof value === 'number' && Number.isFinite(value)
            ? Math.max(size.min, value)
            : size.width,
        ]
      }),
    ) as ColumnWidths
  } catch {
    return { ...DEFAULT_COLUMN_WIDTHS }
  }
}

function ResizableTableHead({
  columnKey,
  width,
  className,
  style,
  title,
  children,
  onResize,
}: {
  columnKey: ColumnKey
  width: number
  className?: string
  style?: CSSProperties
  title?: string
  children: ReactNode
  onResize: (key: ColumnKey, width: number) => void
}) {
  return (
    <TableHead
      data-column-key={columnKey}
      className={cn('relative select-none', className)}
      style={{ ...style, width }}
      title={title}
    >
      {children}
      <ColumnResizeHandle
        minWidth={COLUMN_SIZES[columnKey].min}
        onResize={(nextWidth) => onResize(columnKey, nextWidth)}
      />
    </TableHead>
  )
}

interface ItemsTableProps {
  items: PurchaseRequestItem[]
  /** Bật chế độ sửa: hiện ô nhập + nút thêm/xóa dòng. */
  editing: boolean
  onChange: (items: PurchaseRequestItem[]) => void
  /** SL đã đặt theo MÃ HÀNG, gộp mọi ĐMH sinh từ phiếu (chỉ đọc). */
  orderedByCode?: Record<string, number>
  /** Người yêu cầu / trưởng bộ phận không cần thấy thông tin điều phối nội bộ. */
  showAssignee?: boolean
  onOpenDetail: (index: number) => void

  /** Nhân sự thu mua để chọn NSTM phụ trách — hiện TÊN nhưng lưu MÃ nhân viên. */
  purchasers?: { code: string; name: string }[]
  /** Được phân bổ NSTM phụ trách (quyền duyệt phiếu, phiếu chưa đóng). */
  canAssign?: boolean
  /** Được sửa tiến độ của CHÍNH dòng này (NSTM phụ trách dòng / quản lý). */
  canEditLine?: (item: PurchaseRequestItem) => boolean
  /** Đổi NSTM ngay trên bảng — phiếu đã lưu thì trang tự ghi xuống server. */
  onAssigneeChange?: (item: PurchaseRequestItem, assignee: string) => void
  /** Rời ô "TG dự kiến có hàng": trang hỏi lý do (nếu đổi giá trị đã có) rồi lưu. */
  onExpectedDateCommit?: (
    item: PurchaseRequestItem,
    expectedDate: string,
    originalDate: string,
  ) => void
}

/** Dòng trống khi bấm "Thêm dòng". */
export const EMPTY_PURCHASE_REQUEST_ITEM: PurchaseRequestItem = {
  product_code: '',
  product_name: '',
  item_group: '',
  group_desc: '',
  qty: 0,
  unit: '',
  price: 0,
  vat_pct: 8,
  amount: 0,
  warehouse: '',
  required_date: '',
  assignee: '',
  expected_date: '',
  line_status: 'Chưa đặt hàng',
  progress_note: '',
  note: '',
  qty_ordered: 0,
  qty_received: 0,
  product_id: 0,
  product_thumbnail_url: '',
}

/**
 * Bảng dòng hàng của phiếu YCMH.
 *
 * Thành tiền do BACKEND tính (`amount`), ở đây chỉ tính tạm để người nhập thấy
 * ngay trong lúc gõ — lưu xong sẽ lấy lại số của server.
 */
export function PurchaseRequestItemsTable({
  items,
  editing,
  onChange,
  orderedByCode,
  showAssignee = true,
  onOpenDetail,
  purchasers = [],
  canAssign = false,
  canEditLine,
  onAssigneeChange,
  onExpectedDateCommit,
}: ItemsTableProps) {
  const [columnWidths, setColumnWidths] = useState<ColumnWidths>(readColumnWidths)
  const [bulkDialogOpen, setBulkDialogOpen] = useState(false)
  const [bulkCount, setBulkCount] = useState(5)
  const [historyIndex, setHistoryIndex] = useState<number | null>(null)
  const warehouses = usePurchaseRequestWarehouses(editing)
  const units = usePurchaseRequestUnits(editing)
  const itemGroups = usePurchaseRequestItemGroups(editing)

  function resizeColumn(key: ColumnKey, width: number) {
    setColumnWidths((current) => {
      const next = { ...current, [key]: Math.round(width) }
      try {
        localStorage.setItem(COLUMN_WIDTH_STORAGE_KEY, JSON.stringify(next))
      } catch {
        // Trình duyệt chặn storage thì bảng vẫn đổi cỡ trong phiên hiện tại.
      }
      return next
    })
  }

  function patch(index: number, changes: Partial<PurchaseRequestItem>) {
    onChange(items.map((item, i) => (i === index ? { ...item, ...changes } : item)))
  }

  function groupDescription(name: string) {
    const group = itemGroups.data?.items.find((item) => item.name === name)
    if (!group) return ''
    const parts: string[] = []
    if (group.std_days) parts.push(`Hàng NCC có sẵn: ${group.std_days} ngày`)
    if (group.std_days_unavail) parts.push(`không sẵn: ${group.std_days_unavail} ngày`)
    return parts.join(' · ')
  }

  function applyProduct(index: number, product: ProductOption | null) {
    if (!product) {
      patch(index, { product_id: 0, product_code: '', product_thumbnail_url: '' })
      return
    }
    const current = items[index]
    const itemGroup = product.item_group || current.item_group
    patch(index, {
      product_id: product.id,
      product_code: product.code,
      product_name: product.name,
      product_thumbnail_url: product.thumbnail_url || '',
      unit: product.unit || current.unit,
      item_group: itemGroup,
      group_desc: groupDescription(itemGroup),
    })
  }

  function applyPurchaseHistory(index: number, history: PurchaseHistoryRow) {
    const current = items[index]
    if (!current) return

    const vat = Number(history.vat)
    const itemGroup = history.extra?.item_group?.trim() || current.item_group
    const previousWarehouse = history.extra?.warehouse_code?.trim() || ''
    const warehouse = previousWarehouse
      ? warehouses.data?.items.find(
          (option) =>
            option.code === previousWarehouse || option.name === previousWarehouse,
        )?.name || current.warehouse
      : current.warehouse

    patch(index, {
      unit: history.unit || current.unit,
      qty: Number(history.qty_order) || 0,
      price: Number(history.price) || 0,
      vat_pct: VAT_OPTIONS.some((option) => option === vat) ? vat : current.vat_pct,
      item_group: itemGroup,
      group_desc: groupDescription(itemGroup),
      warehouse,
      note: history.extra?.item_note?.trim() || current.note,
    })
    toast.success('Đã áp dụng dữ liệu từ lịch sử — bấm Lưu để ghi nhận')
  }

  function addMultipleRows() {
    const count = Math.min(50, Math.max(1, Math.trunc(bulkCount) || 1))
    onChange([
      ...items,
      ...Array.from({ length: count }, () => ({ ...EMPTY_PURCHASE_REQUEST_ITEM })),
    ])
    setBulkDialogOpen(false)
    setBulkCount(5)
  }

  const lineTotal = (item: PurchaseRequestItem) =>
    editing ? item.qty * item.price * (1 + (item.vat_pct || 0) / 100) : item.amount

  const pinnedLeft = {
    no: 0,
    code: columnWidths.no,
    name: columnWidths.no + columnWidths.code,
  }
  const visibleColumnKeys: ColumnKey[] = [
    'no',
    'code',
    'name',
    'warehouse',
    'group',
    'unit',
    'qty',
    'price',
    'vat',
    'amount',
    'status',
    'progress',
    'expected',
    ...(showAssignee ? (['assignee'] as const) : []),
    'action',
  ]
  const tableWidth = visibleColumnKeys.reduce((total, key) => total + columnWidths[key], 0)

  return (
    <div className="space-y-3">
      <div className="isolate overflow-hidden rounded-lg border">
        <Table
          className="table-fixed [&_td]:overflow-hidden [&_td]:border-r [&_td]:text-ellipsis [&_td:last-child]:border-r-0 [&_th]:border-r [&_th:last-child]:border-r-0"
          style={{ width: tableWidth, minWidth: tableWidth }}
        >
          <TableHeader className="bg-muted">
            <TableRow className="bg-muted">
              <ResizableTableHead columnKey="no" width={columnWidths.no} className={cn(PINNED.noHead, 'text-center')} style={{ left: pinnedLeft.no }} onResize={resizeColumn}>No.</ResizableTableHead>
              <ResizableTableHead columnKey="code" width={columnWidths.code} className={PINNED.codeHead} style={{ left: pinnedLeft.code }} onResize={resizeColumn}>Mã hàng *</ResizableTableHead>
              <ResizableTableHead columnKey="name" width={columnWidths.name} className={PINNED.nameHead} style={{ left: pinnedLeft.name }} onResize={resizeColumn}>Tên sản phẩm *</ResizableTableHead>
              <ResizableTableHead columnKey="warehouse" width={columnWidths.warehouse} onResize={resizeColumn}>Kho nhận</ResizableTableHead>
              <ResizableTableHead columnKey="group" width={columnWidths.group} onResize={resizeColumn}>Phân loại</ResizableTableHead>
              <ResizableTableHead columnKey="unit" width={columnWidths.unit} onResize={resizeColumn}>ĐVT</ResizableTableHead>
              <ResizableTableHead columnKey="qty" width={columnWidths.qty} className="text-right" onResize={resizeColumn}>SL</ResizableTableHead>
              <ResizableTableHead columnKey="price" width={columnWidths.price} className="text-right" onResize={resizeColumn}>Đơn giá</ResizableTableHead>
              <ResizableTableHead columnKey="vat" width={columnWidths.vat} className="text-right" title="% VAT theo dòng" onResize={resizeColumn}>
                VAT%
              </ResizableTableHead>
              <ResizableTableHead columnKey="amount" width={columnWidths.amount} className="text-right" title="Thành tiền gồm VAT" onResize={resizeColumn}>
                Thành tiền
              </ResizableTableHead>
              <ResizableTableHead columnKey="status" width={columnWidths.status} className="text-center" onResize={resizeColumn}>Trạng thái</ResizableTableHead>
              <ResizableTableHead
                columnKey="progress"
                width={columnWidths.progress}
                className="text-center"
                title="Tổng SL đã nhận / đã đặt, đồng bộ từ Đơn mua hàng"
                onResize={resizeColumn}
              >
                Tiến độ
                <span className="block text-[10.5px] font-normal text-muted-foreground">
                  nhận / đặt
                </span>
              </ResizableTableHead>
              <ResizableTableHead columnKey="expected" width={columnWidths.expected} className="text-center" onResize={resizeColumn}>
                TG dự kiến
                <span className="block text-[10.5px] font-normal text-muted-foreground">
                  có hàng
                </span>
              </ResizableTableHead>
              {showAssignee && <ResizableTableHead columnKey="assignee" width={columnWidths.assignee} onResize={resizeColumn}>NSTM phụ trách</ResizableTableHead>}
              <ResizableTableHead columnKey="action" width={columnWidths.action} className={cn(PINNED.actionHead, 'text-center')} onResize={resizeColumn}>
                Thao tác
              </ResizableTableHead>
            </TableRow>
          </TableHeader>

          <TableBody>
            {items.length === 0 && (
              <TableRow>
                <TableCell
                  colSpan={showAssignee ? 15 : 14}
                  className="py-10 text-center text-muted-foreground"
                >
                  Chưa có sản phẩm nào.
                </TableCell>
              </TableRow>
            )}

            {items.map((item, index) => (
              <TableRow
                key={item.id ?? `new-${index}`}
                // Dòng đã hủy vẫn phải thấy được nhưng không nên tranh sự chú ý.
                className={cn(
                  'group bg-card hover:bg-muted',
                  item.line_status === 'Hủy đơn' && 'opacity-60',
                )}
              >
                <TableCell
                  className={cn(PINNED.noCell, 'text-center text-muted-foreground')}
                  style={{ left: pinnedLeft.no }}
                >
                  {index + 1}
                </TableCell>

                <TableCell className={PINNED.codeCell} style={{ left: pinnedLeft.code }}>
                  {editing ? (
                    <div className="flex min-w-0 items-center gap-1">
                      <div className="min-w-0 flex-1">
                        <PurchaseRequestProductPicker
                          code={item.product_code}
                          name={item.product_name}
                          onPick={(product) => applyProduct(index, product)}
                        />
                      </div>
                      {!!item.product_code && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon-sm"
                          className="shrink-0 text-muted-foreground"
                          title="Xem lịch sử mua hàng gần nhất"
                          aria-label={`Xem lịch sử mua hàng của ${item.product_code}`}
                          onClick={() => setHistoryIndex(index)}
                        >
                          <History />
                        </Button>
                      )}
                    </div>
                  ) : (
                    <span className="block truncate" title={item.product_code}>
                      {item.product_code || '—'}
                    </span>
                  )}
                </TableCell>

                <TableCell className={PINNED.nameCell} style={{ left: pinnedLeft.name }}>
                  {editing ? (
                    <Input
                      value={item.product_name}
                      onChange={(e) => patch(index, { product_name: e.target.value })}
                      placeholder="Tên hàng"
                    />
                  ) : (
                    <span className="block truncate font-medium" title={item.product_name}>
                      {item.product_name}
                    </span>
                  )}
                </TableCell>

                <TableCell>
                  {editing ? (
                    <CatalogSelect
                      value={item.warehouse}
                      placeholder="-- Kho --"
                      options={(warehouses.data?.items ?? []).map((warehouse) => ({
                        value: warehouse.name,
                        label: warehouse.code
                          ? `${warehouse.code} - ${warehouse.name}`
                          : warehouse.name,
                      }))}
                      onChange={(value) => patch(index, { warehouse: value })}
                    />
                  ) : (
                    <span className="block truncate" title={item.warehouse}>
                      {item.warehouse || '—'}
                    </span>
                  )}
                </TableCell>

                <TableCell>
                  {editing ? (
                    <CatalogSelect
                      value={item.item_group}
                      placeholder="-- Phân loại --"
                      options={(itemGroups.data?.items ?? []).map((group) => ({
                        value: group.name,
                        label: group.name,
                      }))}
                      onChange={(value) =>
                        patch(index, {
                          item_group: value,
                          group_desc: groupDescription(value),
                        })
                      }
                    />
                  ) : (
                    <span className="block truncate" title={item.item_group}>
                      {item.item_group || '—'}
                    </span>
                  )}
                </TableCell>

                <TableCell>
                  {editing ? (
                    <CatalogSelect
                      value={item.unit}
                      placeholder="-- ĐVT --"
                      options={(units.data?.items ?? []).map((unit) => ({
                        value: unit.name,
                        label: unit.name,
                      }))}
                      onChange={(value) => patch(index, { unit: value })}
                    />
                  ) : (
                    item.unit || '—'
                  )}
                </TableCell>

                <TableCell className="text-right">
                  {editing ? (
                    <Input
                      className="text-right"
                      type="number"
                      min={0}
                      value={item.qty || ''}
                      onChange={(e) => patch(index, { qty: Number(e.target.value) })}
                    />
                  ) : (
                    <span className="tabular-nums">{formatQuantity(item.qty)}</span>
                  )}
                </TableCell>

                <TableCell className="text-right">
                  {editing ? (
                    <Input
                      className="text-right"
                      type="number"
                      min={0}
                      // Đơn giá cho tới 4 số lẻ (migration d4b9e7c1a305).
                      step="0.0001"
                      value={item.price || ''}
                      onChange={(e) => patch(index, { price: Number(e.target.value) })}
                    />
                  ) : (
                    <span className="tabular-nums">{formatUnitPrice(item.price)}</span>
                  )}
                </TableCell>

                <TableCell className="text-right">
                  {editing ? (
                    <Select
                      value={String(item.vat_pct ?? 8)}
                      onValueChange={(value) => patch(index, { vat_pct: Number(value) })}
                    >
                      <SelectTrigger size="sm" className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent position="popper" align="end">
                        {VAT_OPTIONS.map((vat) => (
                          <SelectItem key={vat} value={String(vat)}>
                            {vat}%
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  ) : (
                    <span className="tabular-nums">{item.vat_pct || 0}%</span>
                  )}
                </TableCell>

                <TableCell className="text-right font-medium tabular-nums">
                  {formatMoney(lineTotal(item))}
                </TableCell>

                <TableCell className="text-center">
                  {/* Dùng chung bảng màu với tiến độ dòng ĐMH: huy hiệu viền
                      trơn khiến "Hủy đơn" và "Hoàn thành" trông y hệt nhau. */}
                  <ProgressStatusBadge status={item.line_status} />
                </TableCell>

                <TableCell className="text-center tabular-nums">
                  {formatQuantity(item.qty_received)} /{' '}
                  {formatQuantity(orderedByCode?.[item.product_code] ?? item.qty_ordered)}
                </TableCell>

                <TableCell className="text-center">
                  {/* Sửa thẳng trên bảng (giống v1): người phụ trách cập nhật
                      tiến độ liên tục, bắt mở hộp chi tiết từng dòng rất mất công. */}
                  {canEditLine?.(item) ? (
                    <DatePicker
                      size="sm"
                      value={item.expected_date || ''}
                      placeholder="Chọn ngày"
                      onChange={(next) => {
                        // Lịch chỉ đổi giá trị khi người dùng thật sự chọn/xóa
                        // ngày, nên gửi đi luôn — không phải chờ rời ô như ô
                        // nhập tay (gõ dở dang thì chưa được gửi).
                        const original = item.expected_date || ''
                        patch(index, { expected_date: next })
                        onExpectedDateCommit?.(item, next, original)
                      }}
                    />
                  ) : (
                    formatDate(item.expected_date) || '—'
                  )}
                </TableCell>

                {showAssignee && (
                  <TableCell>
                    {canAssign ? (
                      <Select
                        value={item.assignee || undefined}
                        onValueChange={(value) => {
                          // Radix Select cấm dùng chuỗi rỗng làm value (rỗng =
                          // "chưa chọn"), nên mục bỏ chọn phải mượn một mã giả
                          // rồi đổi ngược về rỗng ở đây.
                          const assignee = value === UNASSIGNED ? '' : value
                          patch(index, { assignee })
                          onAssigneeChange?.(item, assignee)
                        }}
                      >
                        <SelectTrigger className="h-8 w-full">
                          <SelectValue placeholder="Chọn NSTM" />
                        </SelectTrigger>
                        <SelectContent>
                          {item.assignee && (
                            <SelectItem value={UNASSIGNED} className="text-muted-foreground">
                              — Bỏ chọn —
                            </SelectItem>
                          )}
                          {purchasers.map((purchaser) => (
                            <SelectItem key={purchaser.code} value={purchaser.code}>
                              {purchaser.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    ) : (
                      purchasers.find((purchaser) => purchaser.code === item.assignee)?.name ||
                      item.assignee ||
                      '—'
                    )}
                  </TableCell>
                )}

                <TableCell className={PINNED.actionCell}>
                  <div className="flex items-center justify-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      title="Chi tiết dòng"
                      onClick={() => onOpenDetail(index)}
                    >
                      <Pencil />
                    </Button>
                    {editing && (
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      className="text-destructive hover:text-destructive"
                      title="Xóa dòng"
                      onClick={() => onChange(items.filter((_, i) => i !== index))}
                    >
                      <Trash2 />
                    </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {editing && items.length > 0 && (
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => setBulkDialogOpen(true)}
        >
          Thêm nhiều dòng
        </Button>
      )}

      <Dialog open={bulkDialogOpen} onOpenChange={setBulkDialogOpen}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Thêm nhiều dòng sản phẩm</DialogTitle>
            <DialogDescription>
              Nhập số dòng muốn thêm vào cuối bảng, tối đa 50 dòng mỗi lần.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <label htmlFor="purchase-request-bulk-count" className="text-sm font-medium">
              Số dòng
            </label>
            <Input
              id="purchase-request-bulk-count"
              type="number"
              min={1}
              max={50}
              value={bulkCount}
              onChange={(event) => setBulkCount(Number(event.target.value))}
              onKeyDown={(event) => {
                if (event.key === 'Enter') addMultipleRows()
              }}
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setBulkDialogOpen(false)}>
              Hủy
            </Button>
            <Button type="button" onClick={addMultipleRows}>
              Thêm dòng
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <PurchaseRequestHistoryDialog
        open={historyIndex !== null}
        productCode={historyIndex === null ? '' : items[historyIndex]?.product_code || ''}
        productName={historyIndex === null ? '' : items[historyIndex]?.product_name || ''}
        onOpenChange={(open) => {
          if (!open) setHistoryIndex(null)
        }}
        onPick={(history) => {
          if (historyIndex !== null) applyPurchaseHistory(historyIndex, history)
        }}
      />
    </div>
  )
}

const EMPTY_CATALOG_VALUE = '__empty__'

function CatalogSelect({
  value,
  placeholder,
  options,
  onChange,
}: {
  value: string
  placeholder: string
  options: { value: string; label: string }[]
  onChange: (value: string) => void
}) {
  return (
    <Select
      value={value || EMPTY_CATALOG_VALUE}
      onValueChange={(next) => onChange(next === EMPTY_CATALOG_VALUE ? '' : next)}
    >
      <SelectTrigger size="sm" className="w-full">
        <SelectValue />
      </SelectTrigger>
      <SelectContent position="popper" align="start">
        <SelectItem value={EMPTY_CATALOG_VALUE}>{placeholder}</SelectItem>
        {options.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
