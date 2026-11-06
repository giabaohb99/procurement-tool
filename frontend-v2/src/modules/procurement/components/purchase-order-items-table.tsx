import { useMemo, useState } from 'react'
import { ClipboardList, Copy, History, PauseCircle, Pencil, PlayCircle, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import { UI_ACTION_CODE } from '@/core/telemetry/ui-event-codes'
import { trackUiAction } from '@/core/telemetry/track-ui-action'
import { LinesTable } from '@/shared/data-table/lines-table'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import type { LinesTableSelection } from '@/shared/data-table/lines-table'
import type { LinesTableColumn } from '@/shared/data-table/types'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { CopyButton } from '@/shared/ui/copy-button'
import { Input } from '@/shared/ui/input'
import { NumberInput, PRICE_MAX_DECIMALS } from '@/shared/ui/number-input'
import { SearchSelect } from '@/shared/ui/search-select'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import type {
  ProductOption,
  PurchaseHistoryRow,
} from '../api/purchase-request-support-api'
import {
  usePurchaseRequestItemGroups,
  usePurchaseRequestUnits,
} from '../hooks/use-purchase-request-support'
import { ProgressStatusBadge } from './document-status-badge'
import { PurchaseHistoryDialog } from './purchase-history-dialog'
import { PurchaseOrderItemCard, type PurchaseOrderItemEditField } from './purchase-order-item-card'
import { PurchaseRequestProductPicker } from './purchase-request-product-picker'
import { purchaseOrderRowKey } from '../hooks/use-purchase-order-line-selection'
import {
  isImportOrder,
  isLineLocked,
  isLineReceived,
  PO_VAT_OPTIONS,
  PRODUCT_LOCK_HINT,
  type PurchaseOrderDetail,
  type PurchaseOrderItem,
} from '../types/purchase-order-detail'
import {
  displayLineBaseAmount,
  isMissingExchangeRate,
  resolveLineCurrency,
} from '../utils/purchase-order-import-cost'
import type { LineReportProgress } from '../utils/survey-report-helpers'

/** Thành tiền theo SL ĐẶT — hiện ngay khi gõ, không chờ backend tính lại. */
export function orderLineAmount(item: PurchaseOrderItem): number {
  return (item.qty_order || 0) * (item.price || 0) * (1 + (item.vat || 0) / 100)
}

/**
 * Hậu tố `-v3`: bộ cột vừa đổi (bao-CR-602 thêm cột "Hồ sơ" = tiến độ báo cáo thực
 * hiện theo dòng; `-v2` trước đó thêm Phân loại + Quy đổi VNĐ). `useTableLayout` ưu
 * tiên bố cục đã lưu và nối cột lạ vào cuối, nên bố cục cũ trong `localStorage` sẽ
 * đẩy cột mới xuống cuối bảng. Đổi bộ cột lần sau thì tăng số.
 */
const TABLE_STORAGE_KEY = 'purchase-order-items-v3'

/** Cột của bảng dòng ĐMH TRONG NƯỚC — đơn nhập khẩu lọc bớt / thêm cột ở trên. */
function buildColumns(): LinesTableColumn[] {
  return [
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
      header: 'Mã hàng *',
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
    // Cột Phân loại có ở bản v1; khách đòi lại 09/09/2026 khi xem đơn nhập khẩu.
    {
      key: 'item_group',
      header: 'Phân loại',
      width: 160,
      minWidth: 90,
      compactHidden: true,
      wrap: true,
    },
    { key: 'unit', header: 'ĐVT *', width: 90, minWidth: 50 },
    { key: 'qty', header: 'SL đặt *', width: 108, minWidth: 60, align: 'right' },
    { key: 'price', header: 'Đơn giá *', width: 130, minWidth: 70, align: 'right' },
    {
      key: 'vat',
      header: 'VAT%',
      width: 80,
      minWidth: 50,
      align: 'center',
      compactHidden: true,
    },
    // bao-CR-307: giá một đơn vị ĐÃ gồm VAT — kế toán đối chiếu giá chẵn trên hóa đơn
    {
      key: 'price_after_vat',
      //  140 chứ không phải 130: riêng tiêu đề này đã cần 131px (chữ + `px-2.5`
      //  hai bên), tức là cột hẹp hơn chính cái tên của nó.
      header: 'Đơn giá (Sau VAT)',
      width: 140,
      minWidth: 80,
      align: 'right',
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
    // bao-CR-602: tiến độ BÁO CÁO THỰC HIỆN của dòng (hồ sơ của dòng + hồ sơ chung).
    // Bấm vào là cuộn xuống khối báo cáo và sổ đúng dòng. Không `compactHidden`:
    // đại ca muốn nhìn bảng là thấy ngay dòng nào còn vướng hồ sơ.
    { key: 'report', header: 'Hồ sơ', width: 110, minWidth: 80, align: 'center' },
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
  ]
}

/** Lịch sử có ghi thì lấy, không thì giữ nguyên thứ đang có trên dòng. */
function preferHistory(previous: string, historyValue?: string): string {
  return (historyValue ?? '').trim() || previous || ''
}

interface PurchaseOrderItemsTableProps {
  items: PurchaseOrderItem[]
  /** Sửa được nội dung dòng (đơn chưa chốt + có quyền ghi). */
  editable: boolean
  /**
   * bao-CR-547 — cột tick để "Xóa đã chọn". Trang giữ trạng thái chọn
   * (`usePurchaseOrderLineSelection`) vì nút *Xóa đã chọn (n)* đứng ở tiêu đề thẻ, không
   * nằm trong bảng (duoc-CR-737). Không truyền = không có cột tick.
   */
  selection?: LinesTableSelection<PurchaseOrderItem>
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
  /**
   * bao-CR-319 — loại đơn + đồng tiền / tỷ giá của đơn. Đơn NHẬP KHẨU ẩn cột VAT
   * (thuế GTGT hàng nhập là một khoản chi phí lô hàng) và thêm cột quy đổi VNĐ.
   */
  order?: Pick<PurchaseOrderDetail, 'order_type' | 'currency' | 'exchange_rate'>
  /**
   * bao-CR-602 — tiến độ báo cáo thực hiện theo `item.id` (dòng đã lưu). Không
   * truyền (màn tạo mới) thì cột "Hồ sơ" ẩn hẳn.
   */
  lineReport?: Map<number, LineReportProgress>
  /** Bấm ô "Hồ sơ" của dòng — trang cuộn tới khối báo cáo và sổ nút của dòng đó. */
  onOpenLineReport?: (progress: LineReportProgress) => void
}

const DOMESTIC_ONLY_COLUMNS = new Set(['vat', 'price_after_vat'])

/**
 * duoc-CR-720 — các cột bảng cho sửa tại chỗ mà hộp Chi tiết dòng KHÔNG có. Ở khổ
 * điện thoại không có lưới, nên thẻ dòng phải bày đúng các ô này (xem
 * `PurchaseOrderItemCard`). Thêm ô sửa tại chỗ mới vào bảng mà hộp không có thì
 * thêm khóa vào đây; cột không có trong bộ cột (VAT ở đơn nhập khẩu) tự bị bỏ.
 */
const CARD_INLINE_EDIT_KEYS = ['code', 'qty', 'price', 'vat'] as const

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
  selection,
  progressEditable,
  onChange,
  onProgressChange,
  onOpenDetail,
  onLineRemoved,
  onLineDuplicated,
  order,
  lineReport,
  onOpenLineReport,
}: PurchaseOrderItemsTableProps) {
  const { data: units } = usePurchaseRequestUnits(editable)
  const { data: itemGroups } = usePurchaseRequestItemGroups(editable)
  const itemGroupOptions = useMemo(
    () => (itemGroups?.items ?? []).map((group) => ({ value: group.name, label: group.name })),
    [itemGroups],
  )
  /** Dòng đang xem lịch sử mua hàng; `null` = hộp thoại đang đóng. */
  const [historyIndex, setHistoryIndex] = useState<number | null>(null)
  const importMode = order ? isImportOrder(order) : false
  //  CÙNG `useIsMobile` mà bảng dòng YCMH / YCBG dùng để đổi sang thẻ, nên mọi
  //  bảng dòng chứng từ lật cùng một lúc ở cùng một bề rộng.
  const asCards = useIsMobile()
  const orderCurrency = { currency: order?.currency ?? '', exchange_rate: order?.exchange_rate ?? 0 }

  const columns = useMemo<LinesTableColumn[]>(() => {
    //  Màn tạo mới chưa có dòng đã lưu → không có gì để báo cáo, bỏ cột cho đỡ rối.
    const all = buildColumns().filter((column) => column.key !== 'report' || !!lineReport)
    if (!importMode) return all
    // `useTableLayout` đối chiếu theo khóa nên ẩn/thêm cột lúc chạy là an toàn:
    // khóa `vat` trong bản lưu bị bỏ qua. Chèn `base_amount` ngay sau `amount` để
    // lần đầu mở đơn nhập khẩu đã thấy cột quy đổi nằm cạnh thành tiền.
    const kept = all.filter((column) => !DOMESTIC_ONLY_COLUMNS.has(column.key))
    const amountIndex = kept.findIndex((column) => column.key === 'amount')
    kept.splice(amountIndex + 1, 0, {
      key: 'base_amount',
      header: 'Quy đổi (VNĐ)',
      width: 150,
      minWidth: 80,
      align: 'right',
    })
    return kept
  }, [importMode, lineReport])

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
      // Đơn nhập khẩu giữ VAT dòng = 0 (thuế GTGT nằm ở chi phí lô hàng).
      vat: importMode ? 0 : PO_VAT_OPTIONS.some((option) => option === vat) ? vat : current.vat,
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

  //  Hai hàm dưới dùng chung cho nút ở cột Hành động và nút trên thẻ (khổ điện
  //  thoại) — chép hai nơi là hai chỗ phải nhớ dời giỏ phiếu giao theo chỉ số.
  function duplicateLine(index: number) {
    const item = items[index]
    if (!item) return
    trackUiAction(UI_ACTION_CODE.COPY_LINE)
    onChange([
      ...items.slice(0, index + 1),
      {
        ...item,
        id: undefined,
        deliveries: [],
        qty_received: 0,
        qty_remaining: 0,
        progress_status: 'not_ordered',
        pause_reason: '',
        status_before_pause: '',
      },
      ...items.slice(index + 1),
    ])
    onLineDuplicated?.(index)
  }

  function removeLine(index: number) {
    onChange(items.filter((_, current) => current !== index))
    onLineRemoved?.(index)
  }

  function renderCell(key: string, item: PurchaseOrderItem, index: number) {
    const locked = isLineLocked(item)
    const received = isLineReceived(item)
    const cellEditable = editable && !locked
    const lineCurrency = importMode ? resolveLineCurrency(item, orderCurrency).currency : ''
    const currencySuffix = importMode ? (lineCurrency === 'VND' ? 'đ' : lineCurrency) : 'đ'
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
          <SearchSelect
            searchInTrigger
            wrap
            value={item.unit || ''}
            placeholder="—"
            searchPlaceholder="Tìm đơn vị tính…"
            options={(units?.items ?? []).map((unit) => ({ value: unit.name, label: unit.name }))}
            onChange={(value) => {
              //  Chọn lại đúng mục đang chọn thì thôi — Radix Select cũ không bắn sự kiện.
              if (value === (item.unit || '')) return
              patch(index, { unit: value })
            }}
          />
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

      //  ĐƠN GIÁ giữ tới 4 chữ số lẻ (CR-058) — dùng `formatMoney` là làm tròn tới
      //  đồng ngay trên màn, người dùng tưởng mất số lẻ đã nhập.
      case 'price':
        return (
          <NumberCell
            value={item.price}
            editable={cellEditable}
            onChange={(value) => patch(index, { price: value })}
            format={formatUnitPrice}
            maxDecimals={PRICE_MAX_DECIMALS}
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

      // bao-CR-307: đơn giá sau VAT làm tròn 2 số lẻ — 166.666,67 × 1,08 phải ra
      // 180.000 chứ không phải 180.000,0036
      case 'price_after_vat':
        return (
          <span className="tabular-nums font-semibold">
            {formatUnitPrice(
              Math.round((Number(item.price) || 0) * (1 + (Number(item.vat) || 0) / 100) * 100) /
                100,
            )}
          </span>
        )

      case 'amount':
        return (
          <span className="tabular-nums font-semibold text-navy">
            {importMode && lineCurrency !== 'VND'
              ? formatUnitPrice(orderLineAmount(item))
              : formatMoney(orderLineAmount(item))}{' '}
            {currencySuffix}
          </span>
        )

      // bao-CR-319: thành tiền quy đổi VNĐ — backend trả `base_amount` khi đã lưu,
      // chưa lưu thì tính tại chỗ theo tỷ giá dòng / tỷ giá đơn.
      case 'base_amount':
        return isMissingExchangeRate(item, orderCurrency) ? (
          <span className="text-xs text-warning" title="Nhập tỷ giá ở đầu đơn hoặc trong chi tiết dòng">
            Chưa có tỷ giá
          </span>
        ) : (
          <span className="tabular-nums font-semibold">
            {formatMoney(displayLineBaseAmount(item, orderCurrency))} đ
          </span>
        )

      case 'item_group':
        return cellEditable && !received ? (
          <SearchSelect
            value={item.item_group || ''}
            onChange={(value) => patch(index, { item_group: value })}
            options={itemGroupOptions}
            placeholder="—"
            searchPlaceholder="Tìm phân loại..."
            emptyMessage="Không có phân loại phù hợp"
            clearable
            wrap
          />
        ) : (
          <span className="block break-words whitespace-normal leading-snug">
            {item.item_group || '—'}
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

      case 'report': {
        const progress = item.id ? lineReport?.get(item.id) : undefined
        if (!progress || progress.total === 0) {
          return (
            <span
              className="text-xs text-muted-foreground"
              title={
                item.id
                  ? 'Chưa có hồ sơ báo cáo thực hiện cho dòng này — khởi tạo ở khối Báo cáo thực hiện bên dưới'
                  : 'Lưu đơn rồi mới theo dõi hồ sơ cho dòng mới'
              }
            >
              —
            </span>
          )
        }
        const complete = progress.done === progress.total
        return (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className={cn(
              'h-7 gap-1 px-2 text-xs tabular-nums',
              complete ? 'border-success/40 text-success' : 'text-foreground',
            )}
            title={`${progress.done}/${progress.total} hồ sơ hoàn tất · bấm để xem báo cáo thực hiện của dòng`}
            aria-label={`Hồ sơ dòng ${index + 1}: ${progress.percent}%`}
            onClick={() => onOpenLineReport?.(progress)}
          >
            <ClipboardList className="size-3.5" />
            {progress.percent}%
          </Button>
        )
      }

      case 'status':
        return (
          <LineProgressCell
            item={item}
            controllable={progressEditable && !!item.id && !locked}
            onProgressChange={onProgressChange}
          />
        )

      case 'action':
        return (
          <LineActions
            editable={editable}
            locked={locked}
            onOpenDetail={onOpenDetail ? () => onOpenDetail(index) : undefined}
            onDuplicate={() => duplicateLine(index)}
            onRemove={() => removeLine(index)}
          />
        )

      default:
        return null
    }
  }

  const historyItem = historyIndex === null ? null : items[historyIndex]

  //  Nhãn lấy từ CHÍNH tiêu đề cột (bỏ đuôi " *" rồi vẽ dấu sao riêng) để thẻ và
  //  bảng không lệch tên. Chỉ dòng sửa được (đơn còn sửa + dòng chưa khóa) mới có.
  const cardEditFields = (item: PurchaseOrderItem, index: number): PurchaseOrderItemEditField[] => {
    if (!editable || isLineLocked(item)) return []
    return CARD_INLINE_EDIT_KEYS.flatMap((key) => {
      const column = columns.find((current) => current.key === key)
      if (!column) return []
      const required = column.header.endsWith(' *')
      return [
        {
          key,
          label: required ? column.header.slice(0, -2) : column.header,
          required,
          content: renderCell(key, item, index),
        },
      ]
    })
  }

  return (
    <>
      {asCards ? (
        <div className="space-y-3">
          {/*  Thanh đầu tự dựng như bảng dòng YCMH: ở chế độ thẻ không còn cột nào để
               ẩn/hiện, ghim hay kéo giãn, nên chỉ giữ số dòng + ô chọn tất cả. Nút
               *Xóa đã chọn* ở tiêu đề thẻ của trang (duoc-CR-737). */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium">{items.length} dòng</span>
            {selection && items.length > 0 && (
              <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Checkbox
                  checked={
                    selection.allSelected ? true : selection.someSelected ? 'indeterminate' : false
                  }
                  onCheckedChange={selection.onToggleAll}
                />
                Chọn tất cả
              </label>
            )}
          </div>

          <div className="overflow-hidden rounded-lg border">
            {items.length === 0 ? (
              <p className="px-4 py-8 text-center text-sm text-muted-foreground">
                Chưa có dòng hàng nào.
              </p>
            ) : (
              <div className="divide-y">
                {items.map((item, index) => {
                  const locked = isLineLocked(item)
                  const progress = item.id ? lineReport?.get(item.id) : undefined
                  return (
                    <PurchaseOrderItemCard
                      key={purchaseOrderRowKey(item, index)}
                      item={item}
                      index={index}
                      amount={renderCell('amount', item, index)}
                      baseAmount={importMode ? renderCell('base_amount', item, index) : undefined}
                      progress={
                        <LineProgressCell
                          align="start"
                          item={item}
                          controllable={progressEditable && !!item.id && !locked}
                          onProgressChange={onProgressChange}
                        />
                      }
                      report={
                        progress && progress.total > 0
                          ? renderCell('report', item, index)
                          : undefined
                      }
                      editFields={cardEditFields(item, index)}
                      onOpenDetail={onOpenDetail ? () => onOpenDetail(index) : undefined}
                      selection={
                        selection
                          ? {
                              checked: selection.isSelected(item, index),
                              disabledReason: locked ? selection.unselectableReason : undefined,
                              onToggle: () => selection.onToggle(item, index),
                            }
                          : undefined
                      }
                      actions={
                        <>
                          {/*  Dòng đang sửa thì ô Mã hàng đã kèm nút lịch sử; đừng vẽ hai nút. */}
                          {!!item.product_code && (!editable || locked) && (
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon-sm"
                              className="text-muted-foreground"
                              title="Xem lịch sử mua hàng gần nhất"
                              aria-label={`Xem lịch sử mua hàng của ${item.product_code}`}
                              onClick={() => setHistoryIndex(index)}
                            >
                              <History />
                            </Button>
                          )}
                          <LineActions
                            editable={editable}
                            locked={locked}
                            onDuplicate={() => duplicateLine(index)}
                            onRemove={() => removeLine(index)}
                          />
                        </>
                      }
                    />
                  )
                })}
              </div>
            )}
          </div>
        </div>
      ) : (
        <LinesTable
          columns={columns}
          rows={items}
          storageKey={TABLE_STORAGE_KEY}
          rowKey={purchaseOrderRowKey}
          renderCell={renderCell}
          title={`Danh sách dòng hàng (${items.length} dòng)`}
          emptyMessage="Chưa có dòng hàng nào."
          selection={selection}
          cellClassName={(key) =>
            key === 'amount' || key === 'base_amount' ? 'bg-warning/8' : undefined
          }
        />
      )}

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

/**
 * Ô số: định dạng theo chuẩn Việt (ngăn nghìn bằng dấu chấm) cả lúc nhập lẫn lúc
 * chỉ xem — `<Input type="number">` để số trần nên `1500000` với `150000` nhìn
 * gần như nhau, mà đây là cột đơn giá.
 */
function NumberCell({
  value,
  editable,
  onChange,
  format,
  maxDecimals,
}: {
  value: number
  editable: boolean
  onChange: (value: number) => void
  format: (value: number) => string
  maxDecimals?: number
}) {
  if (!editable) return <span className="tabular-nums">{format(value || 0)}</span>

  return (
    <NumberInput
      className="px-2 text-right"
      value={value ?? 0}
      maxDecimals={maxDecimals}
      onChange={onChange}
    />
  )
}

/**
 * Huy hiệu tiến độ dòng + nút Tạm ngưng / Tiếp tục / Hủy + lý do. Dùng chung cho
 * cột Trạng thái (canh giữa) và thẻ khổ điện thoại (canh trái).
 */
function LineProgressCell({
  item,
  controllable,
  onProgressChange,
  align = 'center',
}: {
  item: PurchaseOrderItem
  /** Đơn đã duyệt trở đi, dòng đã lưu và chưa khóa. */
  controllable: boolean
  onProgressChange?: (item: PurchaseOrderItem, status: string) => void
  align?: 'center' | 'start'
}) {
  return (
    <div className={cn(align === 'center' ? 'text-center' : 'text-left')}>
      <ProgressStatusBadge status={item.progress_status ?? 'not_ordered'} />
      {controllable && (
        <div
          className={cn(
            'mt-1 flex flex-wrap items-center gap-1',
            align === 'center' ? 'justify-center' : 'justify-start',
          )}
        >
          {item.progress_status === 'paused' ? (
            <Button
              type="button"
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
                type="button"
                variant="outline"
                size="sm"
                className="h-7 px-2 text-xs"
                onClick={() => onProgressChange?.(item, 'paused')}
              >
                <PauseCircle />
                Tạm ngưng
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-7 px-2 text-xs text-destructive hover:text-destructive"
                onClick={() => onProgressChange?.(item, 'cancelled')}
              >
                Hủy
              </Button>
            </>
          )}
        </div>
      )}
      {item.pause_reason && ['paused', 'cancelled'].includes(item.progress_status ?? '') && (
        <p className="mt-1 text-xs text-muted-foreground">Lý do: {item.pause_reason}</p>
      )}
    </div>
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
          type="button"
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
          <Button type="button" variant="ghost" size="icon-sm" title="Nhân bản dòng" onClick={onDuplicate}>
            <Copy />
          </Button>
          <Button
            type="button"
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
