import { useMemo, useState } from 'react'
import { History, Pencil, Plus, PlusCircle, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import { LinesTable } from '@/shared/data-table/lines-table'
import type { LinesTableColumn } from '@/shared/data-table/types'
import { Button } from '@/shared/ui/button'
import { CopyButton } from '@/shared/ui/copy-button'
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
import { PurchaseHistoryDialog } from './purchase-history-dialog'
import { PurchaseRequestProductPicker } from './purchase-request-product-picker'

/** Mã giả cho mục "bỏ chọn NSTM" — xem chú thích ở ô chọn NSTM. */
const UNASSIGNED = '__unassigned__'

const TABLE_STORAGE_KEY = 'purchase-request-items'

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
  /** Phiếu đang ở trạng thái còn sửa nội dung được (nháp / bị trả lại). */
  documentEditable?: boolean
  /** Bật chế độ sửa của cả phiếu ngay từ bảng, khỏi đi tìm nút Sửa trên đầu trang. */
  onStartEditing?: () => void

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
  line_status: 'no_po',   // B-06: MÃ, khớp mặc định của backend
  progress_note: '',
  note: '',
  qty_ordered: 0,
  qty_received: 0,
  product_id: 0,
  product_thumbnail_url: '',
}

/**
 * Bảng dòng hàng của phiếu YCMH với hỗ trợ:
 * - Ghim cột cố định (default: No, Code, Name).
 * - Kéo thả trực tiếp tiêu đề cột trên bảng để đổi thứ tự.
 * - Chế độ Bảng rút gọn vs Bảng đầy đủ.
 * - Kéo giãn / co nhỏ độ rộng cột & nhớ tự động vào localStorage.
 */
export function PurchaseRequestItemsTable({
  items,
  editing,
  onChange,
  orderedByCode,
  showAssignee = true,
  onOpenDetail,
  documentEditable = false,
  onStartEditing,
  purchasers = [],
  canAssign = false,
  canEditLine,
  onAssigneeChange,
  onExpectedDateCommit,
}: ItemsTableProps) {
  const [bulkDialogOpen, setBulkDialogOpen] = useState(false)
  const [bulkCount, setBulkCount] = useState(5)
  const [historyIndex, setHistoryIndex] = useState<number | null>(null)
  const warehouses = usePurchaseRequestWarehouses(editing)
  const units = usePurchaseRequestUnits(editing)
  const itemGroups = usePurchaseRequestItemGroups(editing)

  const columns = useMemo<LinesTableColumn[]>(() => [
    {
      key: 'no',
      header: 'No.',
      width: 48,
      minWidth: 40,
      hideable: false,
      defaultPinned: true,
      align: 'center',
    },
    {
      key: 'code',
      header: 'Mã hàng *',
      // Rộng hơn bề ngang của mã: ô còn chứa nút chép mã và nút lịch sử mua hàng.
      width: 196,
      minWidth: 90,
      hideable: false,
      defaultPinned: true,
    },
    {
      key: 'name',
      header: 'Tên sản phẩm *',
      width: 300,
      minWidth: 140,
      hideable: false,
      defaultPinned: true,
    },
    {
      key: 'warehouse',
      header: 'Kho nhận *',
      width: 220,
      minWidth: 100,
      compactHidden: true,
    },
    {
      key: 'group',
      header: 'Phân loại',
      width: 180,
      minWidth: 100,
      compactHidden: true,
    },
    { key: 'unit', header: 'ĐVT', width: 80, minWidth: 50 },
    { key: 'qty', header: 'SL *', width: 88, minWidth: 50, align: 'right' },
    { key: 'price', header: 'Đơn giá', width: 112, minWidth: 70, align: 'right' },
    {
      key: 'vat',
      header: 'VAT %',
      width: 72,
      minWidth: 50,
      align: 'right',
      compactHidden: true,
    },
    { key: 'amount', header: 'Thành tiền', width: 130, minWidth: 80, align: 'right' },
    { key: 'status', header: 'Trạng thái', width: 190, minWidth: 120, align: 'center' },
    {
      key: 'progress',
      header: 'Tiến độ',
      width: 112,
      minWidth: 70,
      align: 'center',
      compactHidden: true,
    },
    {
      key: 'expected',
      header: 'TG dự kiến',
      width: 170,
      minWidth: 130,
      align: 'center',
      compactHidden: true,
    },
    ...(showAssignee
      ? [
          {
            key: 'assignee',
            header: 'NSTM phụ trách',
            width: 210,
            minWidth: 140,
            compactHidden: true,
          },
        ]
      : []),
    {
      key: 'action',
      header: 'Thao tác',
      width: 88,
      minWidth: 60,
      hideable: false,
      align: 'center',
    },
  ], [showAssignee])

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

  function renderCell(key: string, item: PurchaseRequestItem, index: number) {
    switch (key) {
      case 'no':
        return <span className="text-muted-foreground">{index + 1}</span>

      case 'code':
        return (
          <div className="flex min-w-0 items-center gap-0.5">
            <div className="min-w-0 flex-1">
              {editing ? (
                <PurchaseRequestProductPicker
                  code={item.product_code}
                  name={item.product_name}
                  onPick={(product) => applyProduct(index, product)}
                />
              ) : (
                <span
                  className="block break-words whitespace-normal leading-snug font-medium"
                  title={item.product_code}
                >
                  {item.product_code || '—'}
                </span>
              )}
            </div>
            {/* Đang sửa thì mã nằm trong ô chọn (một <button>) nên bôi đen không
                được — nút chép là đường duy nhất lấy được mã ra ngoài. */}
            <CopyButton value={item.product_code} label="mã hàng" className="size-7" />
            {editing && !!item.product_code && (
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
        return editing ? (
          <Input
            value={item.product_name}
            onChange={(e) => patch(index, { product_name: e.target.value })}
            placeholder="Tên hàng"
          />
        ) : (
          <span className="block break-words whitespace-normal font-medium leading-snug" title={item.product_name}>
            {item.product_name}
          </span>
        )

      case 'warehouse':
        return editing ? (
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
          <span className="block break-words whitespace-normal leading-snug" title={item.warehouse}>
            {item.warehouse || '—'}
          </span>
        )

      case 'group':
        return editing ? (
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
          <span className="block break-words whitespace-normal leading-snug" title={item.item_group}>
            {item.item_group || '—'}
          </span>
        )

      case 'unit':
        return editing ? (
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
        )

      case 'qty':
        return editing ? (
          <Input
            className="text-right"
            type="number"
            min={0}
            value={item.qty || ''}
            onChange={(e) => patch(index, { qty: Number(e.target.value) })}
          />
        ) : (
          <span className="tabular-nums">{formatQuantity(item.qty)}</span>
        )

      case 'price':
        return editing ? (
          <Input
            className="text-right"
            type="number"
            min={0}
            step="0.0001"
            value={item.price || ''}
            onChange={(e) => patch(index, { price: Number(e.target.value) })}
          />
        ) : (
          <span className="tabular-nums">{formatUnitPrice(item.price)}</span>
        )

      case 'vat':
        return editing ? (
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
        )

      case 'amount':
        return (
          <span className="tabular-nums font-semibold text-navy">
            {formatMoney(lineTotal(item))}
          </span>
        )

      case 'status':
        return (
          <div className="flex items-center justify-center">
            <ProgressStatusBadge status={item.line_status} />
          </div>
        )

      case 'progress':
        return (
          <span className="tabular-nums">
            {formatQuantity(item.qty_received)} /{' '}
            {formatQuantity(orderedByCode?.[item.product_code] ?? item.qty_ordered)}
          </span>
        )

      case 'expected':
        return canEditLine?.(item) ? (
          <DatePicker
            size="sm"
            value={item.expected_date || ''}
            placeholder="Chọn ngày"
            onChange={(next) => {
              const original = item.expected_date || ''
              patch(index, { expected_date: next })
              onExpectedDateCommit?.(item, next, original)
            }}
          />
        ) : (
          <span className="tabular-nums">{formatDate(item.expected_date) || '—'}</span>
        )

      case 'assignee':
        return canAssign ? (
          <Select
            value={item.assignee || undefined}
            onValueChange={(value) => {
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
          <span className="block break-words whitespace-normal leading-snug">
            {purchasers.find((purchaser) => purchaser.code === item.assignee)?.name ||
              item.assignee ||
              '—'}
          </span>
        )

      case 'action':
        return (
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
        )

      default:
        return null
    }
  }

  return (
    <>
      <LinesTable
        columns={columns}
        rows={items}
        storageKey={TABLE_STORAGE_KEY}
        rowKey={(item, index) => item.id ?? `new-${index}`}
        renderCell={renderCell}
        title={`Danh sách sản phẩm (${items.length} dòng)`}
        emptyMessage="Chưa có sản phẩm nào."
        rowClassName={(item) =>
          item.line_status === 'cancelled' ? 'opacity-60' : undefined
        }
        actions={
          editing ? (
            <>
              <Button
                type="button"
                size="sm"
                onClick={() => onChange([...items, { ...EMPTY_PURCHASE_REQUEST_ITEM }])}
              >
                <Plus /> Thêm dòng
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => setBulkDialogOpen(true)}
              >
                <PlusCircle /> Thêm nhiều
              </Button>
            </>
          ) : (
            /*
              Phiếu nháp mà bảng vẫn là chữ chết thì người dùng tưởng mình hết
              quyền — nút Sửa duy nhất lại nằm tít trên đầu trang, lẫn giữa gần
              chục nút khác. Đặt lối vào ngay cạnh bảng, đúng chỗ đang nhìn.
            */
            documentEditable &&
            onStartEditing && (
              <Button type="button" size="sm" variant="outline" onClick={onStartEditing}>
                <Pencil /> Sửa dòng hàng
              </Button>
            )
          )
        }
      />

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

      <PurchaseHistoryDialog
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
    </>
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
