import { useMemo, useState, type ReactNode } from 'react'
import { Copy, History, Pencil, PlusCircle, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import { LinesTable } from '@/shared/data-table/lines-table'
import { useLineSelection } from '@/shared/hooks/use-line-selection'
import { BulkDeleteButton } from '@/shared/ui/bulk-delete-button'
import type { LinesTableColumn } from '@/shared/data-table/types'
import { useIsMobile } from '@/shared/hooks/use-mobile'
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
import { SearchSelect } from '@/shared/ui/search-select'
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
import { resolveCatalogSelection } from '../utils/catalog-selection'
import {
  VAT_OPTIONS,
  type PurchaseRequestItem,
} from '../types/purchase-request-detail'
import { ProgressStatusBadge } from './document-status-badge'
import { PurchaseHistoryDialog } from './purchase-history-dialog'
import { PurchaseRequestLineCard } from './purchase-request-line-card'
import { PurchaseRequestProductPicker } from './purchase-request-product-picker'

const TABLE_STORAGE_KEY = 'purchase-request-items'

//  Khóa dòng: dòng chưa lưu chưa có id nên lấy chỉ số — khai cấp module để tham chiếu không đổi.
function purchaseRequestRowKey(item: PurchaseRequestItem, index: number): string | number {
  return item.id ?? `new-${index}`
}

interface ItemsTableProps {
  items: PurchaseRequestItem[]
  /** Bật chế độ sửa: hiện ô nhập + nút thêm/xóa dòng. */
  editing: boolean
  onChange: (items: PurchaseRequestItem[]) => void
  /**
   * bao-CR-547 — cho tick nhiều dòng rồi "Xóa đã chọn". Trang bật khi phiếu là form tạo hoặc
   * đang Nháp (đại ca chốt 01/10/2026); phiếu Bị trả lại vẫn xóa từng dòng như cũ.
   */
  bulkRemovable?: boolean
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
  /**
   * duoc-CR-737 — cụm nút của bảng đứng ở GÓC PHẢI TIÊU ĐỀ THẺ như bản v1, không ở
   * thanh tiêu đề của `LinesTable`. Bảng giữ state tick dòng nên trao hai mảnh cho
   * trang tự xếp vào khung `Card`: `headerActions` (*Xóa đã chọn (n)*, chỉ dựng khi có
   * dòng đang tick) và `body` (bảng + nút *Thêm nhiều dòng* bên dưới). Bỏ trống thì hai
   * mảnh đứng liền nhau.
   */
  renderFrame?: (parts: { headerActions: ReactNode; body: ReactNode }) => ReactNode
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
  bulkRemovable = false,
  orderedByCode,
  showAssignee = true,
  onOpenDetail,
  purchasers = [],
  canAssign = false,
  canEditLine,
  onAssigneeChange,
  onExpectedDateCommit,
  renderFrame = ({ headerActions, body }) => (
    <>
      {headerActions}
      {body}
    </>
  ),
}: ItemsTableProps) {
  const [bulkDialogOpen, setBulkDialogOpen] = useState(false)
  const lineSelection = useLineSelection({
    rows: items,
    rowKey: purchaseRequestRowKey,
    enabled: editing && bulkRemovable,
  })
  const removeSelectedLines = () => {
    const drop = new Set(lineSelection.selectedIndexes)
    onChange(items.filter((_, index) => !drop.has(index)))
    lineSelection.clear()
  }
  //  Nhân đôi / xóa MỘT dòng làm các dòng phía sau trôi chỉ số. Dòng chưa lưu khóa theo chỉ
  //  số (`new-${index}`), nên dấu tick đang đặt ở dòng 4 sẽ nhảy sang dòng 3 cũ vừa trôi
  //  xuống, và *Xóa đã chọn* xóa nhầm dòng (rà mã duoc-CR-741). Bỏ hết dấu tick cho chắc.
  const duplicateLineAt = (index: number) => {
    onChange(duplicateLine(items, index))
    lineSelection.clear()
  }
  const removeLineAt = (index: number) => {
    onChange(items.filter((_, i) => i !== index))
    lineSelection.clear()
  }
  const [bulkCount, setBulkCount] = useState(5)
  const [historyIndex, setHistoryIndex] = useState<number | null>(null)
  const warehouses = usePurchaseRequestWarehouses(editing)
  const units = usePurchaseRequestUnits(editing)
  const itemGroups = usePurchaseRequestItemGroups(editing)

  //  CÙNG một `useIsMobile` mà `DataTable` và bảng dòng khảo sát dùng để đổi
  //  sang thẻ, nên hai lối bày dữ liệu của cả hệ luôn lật cùng một lúc.
  const asCards = useIsMobile()

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
    {
      // QA 29/08: ngày cần hàng trước đây chỉ nằm trong popup Chi tiết dòng,
      // người tạo phiếu không thấy chỗ chọn — kéo hẳn ra bảng, KHÔNG ẩn ở
      // chế độ rút gọn vì đây là trường bắt buộc khi gửi duyệt.
      key: 'required',
      header: 'Ngày cần hàng *',
      control: 'date',
      width: 170,
      align: 'center',
    },
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
      control: 'date',
      width: 170,
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
      //  Ba nút lúc sửa (Chi tiết · Nhân đôi · Xóa, duoc-CR-741) — 88px cũ chỉ đủ hai.
      width: 112,
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
            {/* bao-CR-320: phiếu đã khóa vẫn xem được lịch sử (chỉ xem, không điền giá). */}
            {!!item.product_code && (
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                className="size-7 shrink-0 text-muted-foreground"
                title={purchaseHistoryTooltip(editing)}
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

      case 'required':
        return editing ? (
          <DatePicker
            size="sm"
            value={item.required_date || ''}
            placeholder="Chọn ngày"
            onChange={(next) => patch(index, { required_date: next })}
          />
        ) : (
          <span className="tabular-nums">{formatDate(item.required_date) || '—'}</span>
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
          //  "Bỏ chọn" cũ nay là nút xóa của ô (trả về `''`), chỉ hiện khi đang có người.
          <SearchSelect
            searchInTrigger
            clearable
            wrap
            size="sm"
            value={item.assignee || ''}
            placeholder="Chọn NSTM"
            searchPlaceholder="Gõ để tìm NSTM…"
            options={purchasers.map((purchaser) => ({
              value: purchaser.code,
              label: purchaser.name,
            }))}
            onChange={(assignee) => {
              //  Chọn lại đúng người đang gán thì thôi — Radix Select cũ không bắn sự kiện,
              //  mà `onAssigneeChange` là một lần gọi API phân công.
              if (assignee === (item.assignee || '')) return
              patch(index, { assignee })
              onAssigneeChange?.(item, assignee)
            }}
          />
        ) : (
          <span className="block break-words whitespace-normal leading-snug">
            {item.assignee_name ||
              purchasers.find((purchaser) => purchaser.code === item.assignee)?.name ||
              item.assignee ||
              '—'}
          </span>
        )

      case 'action':
        return (
          <div className="flex items-center justify-center gap-1">
            {/*  duoc-CR-741: gợi ý đúng chữ v1 (*Chi tiết* · *Nhân đôi* · *Xóa*). Tên đọc
                 cho trình đọc màn hình kèm số dòng để mỗi nút vẫn tìm được riêng. */}
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              title="Chi tiết"
              aria-label={`Chi tiết dòng ${index + 1}`}
              onClick={() => onOpenDetail(index)}
            >
              <Pencil />
            </Button>
            {editing && (
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                className="text-muted-foreground"
                title="Nhân đôi"
                aria-label={`Nhân đôi dòng ${index + 1}`}
                onClick={() => duplicateLineAt(index)}
              >
                <Copy />
              </Button>
            )}
            {editing && (
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                className="text-destructive hover:text-destructive"
                title="Xóa"
                aria-label={`Xóa dòng ${index + 1}`}
                onClick={() => removeLineAt(index)}
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

  // Nút "Sửa dòng hàng" cũ đã bỏ (QA 29/08): phiếu còn sửa được thì trang mở
  // thẳng chế độ sửa, bảng nhập trực tiếp như bản v1.
  //
  // duoc-CR-737: thanh nút cũ trên tiêu đề `LinesTable` (Thêm dòng · Thêm nhiều ·
  // Xóa đã chọn) tách về đúng chỗ của v1 — *Xóa đã chọn* lên góc phải tiêu đề thẻ
  // (cạnh *Thêm SP* của trang), *Thêm nhiều dòng* xuống dưới bảng. *Thêm dòng* bỏ hẳn:
  // nó làm đúng việc của *Thêm SP* trên tiêu đề thẻ (thêm một dòng trống cuối bảng),
  // để cả hai là hai nút cùng một lệnh đứng cách nhau một hàng.
  const bulkDeleteAction = (
    <BulkDeleteButton
      size="sm"
      count={lineSelection.selectedIndexes.length}
      unitLabel="dòng"
      //  duoc-CR-741: câu và nút của v1 — *Xóa n dòng đã chọn? Dòng bỏ khỏi phiếu ngay trên
      //  màn hình, bấm Lưu mới ghi xuống.* · nút *Đồng ý* / *Hủy*.
      title="Xác nhận"
      description={`Xóa ${lineSelection.selectedIndexes.length} dòng đã chọn? Dòng bỏ khỏi phiếu ngay trên màn hình, bấm Lưu mới ghi xuống.`}
      confirmLabel="Đồng ý"
      onConfirm={removeSelectedLines}
    />
  )
  const addManyAction = editing && (
    <div className="flex">
      <Button type="button" size="sm" variant="outline" onClick={() => setBulkDialogOpen(true)}>
        <PlusCircle /> Thêm nhiều dòng
      </Button>
    </div>
  )

  const body = (
    <>
      {asCards ? (
        <div className="space-y-3">
          {/*  Thanh đầu tự dựng lại chứ không mượn của `LinesTable`: ở chế độ thẻ
               không còn cột nào để ẩn/hiện, ghim hay kéo giãn, nên ba nút *Bảng
               đầy đủ · Vừa nội dung · Cột* là mời người dùng bấm vào một bảng
               điều khiển không điều khiển thứ gì đang nhìn thấy — cùng luật đã áp
               cho bảng dòng khảo sát. */}
          {/*  Chỉ đếm dòng, KHÔNG lặp lại "Danh sách sản phẩm": thẻ bọc ngoài đã
               có tiêu đề *Danh sách Sản phẩm Yêu cầu* ngay bên trên, ở khổ hẹp hai
               dòng chữ gần giống nhau xếp chồng đọc như bị lặp. */}
          <span className="block text-sm font-medium">{items.length} dòng</span>

          <div className="overflow-hidden rounded-lg border">
            {items.length === 0 ? (
              <p className="px-4 py-8 text-center text-sm text-muted-foreground">
                Chưa có sản phẩm nào.
              </p>
            ) : (
              <div className="divide-y">
                {items.map((item, index) => (
                  <PurchaseRequestLineCard
                    key={item.id ?? `new-${index}`}
                    item={item}
                    index={index}
                    editing={editing}
                    amount={lineTotal(item)}
                    ordered={orderedByCode?.[item.product_code] ?? item.qty_ordered}
                    showAssignee={showAssignee}
                    assigneeName={
                      item.assignee_name ||
                      purchasers.find((purchaser) => purchaser.code === item.assignee)?.name ||
                      item.assignee
                    }
                    onOpenDetail={() => onOpenDetail(index)}
                    onOpenHistory={() => setHistoryIndex(index)}
                    onDuplicate={() => duplicateLineAt(index)}
                    onRemove={() => removeLineAt(index)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      ) : (
        <LinesTable
          columns={columns}
          rows={items}
          storageKey={TABLE_STORAGE_KEY}
          rowKey={purchaseRequestRowKey}
          renderCell={renderCell}
          title={`Danh sách sản phẩm (${items.length} dòng)`}
          selection={lineSelection.selection}
          emptyMessage="Chưa có sản phẩm nào."
          rowClassName={(item) =>
            item.line_status === 'cancelled' ? 'opacity-60' : undefined
          }
        />
      )}
      {addManyAction}
    </>
  )

  return (
    <>
      {renderFrame({ headerActions: bulkDeleteAction, body })}

      <Dialog open={bulkDialogOpen} onOpenChange={setBulkDialogOpen}>
        <DialogContent className="sm:max-w-sm">
          {/*  duoc-CR-741: hộp hỏi của v1 (`askPrompt`) — tiêu đề *Nhập thông tin*, câu
               *Thêm bao nhiêu dòng?*, nút *Xác nhận* / *Hủy*. Trần 50 dòng mỗi lần giữ lại
               của v2 để gõ nhầm 5000 không đẻ ra cả nghìn dòng trống. */}
          <DialogHeader>
            <DialogTitle>Nhập thông tin</DialogTitle>
            <DialogDescription>Thêm bao nhiêu dòng?</DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <label htmlFor="purchase-request-bulk-count" className="sr-only">
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
              Xác nhận
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <PurchaseHistoryDialog
        open={historyIndex !== null}
        readOnly={!editing}
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

/**
 * Gợi ý của nút lịch sử mua hàng — đúng chữ v1 (duoc-CR-741). Phiếu đã khóa vẫn mở được
 * nhưng chỉ xem, không điền giá vào dòng (bao-CR-320).
 */
function purchaseHistoryTooltip(editing: boolean): string {
  return editing
    ? 'Lịch sử mua hàng gần nhất của mã hàng này'
    : 'Lịch sử mua hàng gần nhất của mã hàng này (chỉ xem)'
}

/**
 * Nút *Nhân đôi* của v1 (`copyItem`, duoc-CR-741): chèn bản sao NGAY SAU dòng gốc.
 *
 * Bỏ `id` vì bản sao là dòng khác — giữ id thì lúc lưu backend ghi đè dòng gốc. Bỏ luôn
 * phần phương án (bao-CR-310) vì phương án gắn theo id dòng, chép sang là bản sao trỏ
 * vào phương án của dòng gốc. Ảnh đối chiếu cũng không đi theo (ảnh gắn theo id dòng).
 */
function duplicateLine(items: PurchaseRequestItem[], index: number): PurchaseRequestItem[] {
  const source = items[index]
  if (!source) return items
  const copy: PurchaseRequestItem = {
    ...source,
    id: undefined,
    option_count: undefined,
    chosen_option: undefined,
    options_done: undefined,
    no_option: undefined,
  }
  return [...items.slice(0, index + 1), copy, ...items.slice(index + 1)]
}

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
  const resolved = resolveCatalogSelection(value, options)
  //  Mục "-- Kho --" / "-- ĐVT --" cũ (chọn để bỏ trống) nay là nút xóa của ô, cũng trả `''`.
  return (
    <SearchSelect
      searchInTrigger
      clearable
      wrap
      size="sm"
      value={resolved.selected}
      placeholder={placeholder}
      searchPlaceholder="Gõ để tìm…"
      options={resolved.options}
      onChange={(next) => {
        //  Chọn lại đúng mục đang chọn thì thôi — Radix Select cũ không bắn sự kiện.
        if (next === resolved.selected) return
        onChange(next)
      }}
    />
  )
}
