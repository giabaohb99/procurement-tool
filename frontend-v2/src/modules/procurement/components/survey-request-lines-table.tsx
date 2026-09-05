import { useMemo, useState } from 'react'
import { Copy, History, Pencil, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import { LinesTable } from '@/shared/data-table/lines-table'
import { cn } from '@/shared/utils/cn'
import type { LinesTableColumn } from '@/shared/data-table/types'
import { Button } from '@/shared/ui/button'
import { CopyButton } from '@/shared/ui/copy-button'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { Textarea } from '@/shared/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import type {
  ProductOption,
  PurchaseHistoryRow,
} from '../api/purchase-request-support-api'
import {
  usePurchaseRequestItemGroups,
  usePurchaseRequestUnits,
  usePurchaseRequestWarehouses,
} from '../hooks/use-purchase-request-support'
import { VAT_OPTIONS } from '../types/purchase-request-detail'
import type { SurveyRequestLine } from '../types/survey-request-detail'
import { SurveyLineStateBadge } from './document-status-badge'
import { PurchaseHistoryDialog } from './purchase-history-dialog'
import { PurchaseRequestProductPicker } from './purchase-request-product-picker'

/** Dòng trống khi bấm "Thêm dòng". */
export const EMPTY_SURVEY_REQUEST_LINE: SurveyRequestLine = {
  item_group: '',
  requirement_detail: '',
  other_requirement: '',
  request_qty: 0,
  uom: '',
  proposed_price: 0,
  product_code: '',
  warehouse: '',
  required_date: '',
  // bao-CR-289: mặc định 8% như dòng YCMH — 0 vẫn chọn được cho hàng không chịu thuế.
  vat_pct: 8,
  qty_ordered: 0,
  qty_received: 0,
  expected_date: '',
  progress_note: '',
  purchaser_note: '',
  received_date: '',
  result_due_date: '',
  result_date: '',
  assignee: '',
  assignee_name: '',
  pr_id: 0,
  pr_code: '',
  po_id: 0,
  po_code: '',
  is_completed: false,
  line_status: '',
  no_option: false,
  option_count: 0,
  has_chosen: false,
  progress_state: '',
  progress_tone: 'gray',
}

/** Mã giả cho mục "bỏ chọn NSTM" — Radix Select cấm dùng chuỗi rỗng làm value. */
const UNASSIGNED = '__unassigned__'
const EMPTY_CATALOG_VALUE = '__empty__'

// bao-CR-289: đổi khóa để bố cục cũ trong localStorage không đè lên bộ cột mới
// — giữ khóa cũ là cột Mã hàng/Kho nhận/VAT... bị ẩn theo bản nhớ cũ.
// v3: nới bề rộng mặc định ĐVT/VAT (góp ý 04/09), phải đổi khóa lần nữa vì bản
// nhớ v2 đã ghi bề rộng hẹp cũ.
const TABLE_STORAGE_KEY = 'survey-request-lines-v3'

interface SurveyRequestLinesTableProps {
  lines: SurveyRequestLine[]
  editing: boolean
  /** Cột nội bộ của thu mua (ngày tiếp nhận, NSTM) — người yêu cầu không thấy. */
  showNstmColumns: boolean
  /** Cột tiến độ dòng: phiếu chưa lưu thì chưa có gì để hiện. */
  showStatus: boolean
  canAssignNstm: boolean
  /**
   * Ô đang thiếu nội dung sau lần bấm Gửi duyệt gần nhất — khóa dạng
   * `line-${index}-item_group` (xem `invalidSurveyRequestKeys`). Tô đỏ để
   * người lập thấy ngay dòng nào hụt thay vì dò theo câu toast.
   */
  invalid?: Set<string>
  /** NSTM chọn được — hiện TÊN nhưng lưu MÃ nhân sự. */
  purchasers: { code: string; name: string }[]
  onChange: (lines: SurveyRequestLine[]) => void
  onOpenDetail: (index: number) => void
  /** Đổi NSTM ngay trên bảng — trang tự ghi xuống server, không chờ nút Lưu. */
  onAssigneeChange: (line: SurveyRequestLine, assignee: string) => void
  /**
   * Xóa / nhân bản dòng làm lệch chỉ số của mọi dòng phía sau. Trang đang giữ hộ
   * hình của dòng chưa lưu theo chỉ số nên phải biết chỗ vừa đổi mà dời khóa.
   */
  onLineRemoved?: (index: number) => void
  onLineDuplicated?: (index: number) => void
}

/**
 * Bảng "Danh sách sản phẩm cần khảo sát" hỗ trợ:
 * - Ghim cột cố định (default: No, Phân loại, Chi tiết thông số).
 * - Kéo thả trực tiếp tiêu đề cột trên bảng để đổi thứ tự.
 * - Chế độ Bảng rút gọn vs Bảng đầy đủ.
 * - Kéo giãn / co nhỏ độ rộng cột & nhớ tự động vào localStorage.
 */
export function SurveyRequestLinesTable({
  lines,
  editing,
  showNstmColumns,
  showStatus,
  canAssignNstm,
  invalid,
  purchasers,
  onChange,
  onOpenDetail,
  onAssigneeChange,
  onLineRemoved,
  onLineDuplicated,
}: SurveyRequestLinesTableProps) {
  const units = usePurchaseRequestUnits(editing)
  const itemGroups = usePurchaseRequestItemGroups(editing)
  const warehouses = usePurchaseRequestWarehouses(editing)
  const [historyIndex, setHistoryIndex] = useState<number | null>(null)

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
      // bao-CR-289: mã hàng chọn được ngay lúc lập phiếu — KHÔNG bắt buộc,
      // dòng chưa có mã sẽ được điền khi người YC chốt phương án mang mã (P6-2).
      key: 'product_code',
      header: 'Mã hàng',
      // Rộng hơn bề ngang của mã: ô còn chứa nút chép mã và nút lịch sử mua hàng.
      width: 196,
      minWidth: 90,
      defaultPinned: true,
    },
    {
      key: 'requirement_detail',
      header: 'Chi tiết thông số',
      width: 300,
      minWidth: 140,
      defaultPinned: true,
    },
    {
      key: 'item_group',
      header: 'Phân loại *',
      width: 170,
      minWidth: 100,
    },
    {
      key: 'warehouse',
      header: 'Kho nhận *',
      width: 200,
      minWidth: 100,
      compactHidden: true,
    },
    ...(showNstmColumns
      ? [
          {
            key: 'received_date',
            header: 'Ngày tiếp nhận',
            width: 130,
            minWidth: 90,
            compactHidden: true,
          },
        ]
      : []),
    {
      key: 'result_due_date',
      header: 'Ngày YC trả KQ',
      width: 140,
      minWidth: 100,
      compactHidden: true,
    },
    // ĐVT + VAT nới hơn mặc định gốc theo góp ý 04/09 — 90/72px làm chữ wrap.
    { key: 'uom', header: 'ĐVT', width: 120, minWidth: 70 },
    { key: 'request_qty', header: 'SL dự kiến *', width: 110, minWidth: 50, align: 'right' },
    {
      key: 'proposed_price',
      header: 'Giá đề xuất',
      width: 130,
      minWidth: 70,
      align: 'right',
      compactHidden: true,
    },
    {
      key: 'vat',
      header: 'VAT %',
      width: 104,
      minWidth: 70,
      align: 'right',
      compactHidden: true,
    },
    { key: 'amount', header: 'Thành tiền', width: 130, minWidth: 80, align: 'right' },
    {
      key: 'required_date',
      header: 'Ngày cần hàng *',
      width: 170,
      minWidth: 130,
      align: 'center',
    },
    {
      key: 'progress',
      header: 'Tiến độ nhận/đặt',
      width: 130,
      minWidth: 70,
      align: 'center',
      compactHidden: true,
    },
    {
      key: 'expected',
      header: 'Ngày dự kiến có hàng',
      width: 150,
      minWidth: 100,
      align: 'center',
      compactHidden: true,
    },
    ...(showNstmColumns
      ? [
          {
            key: 'assignee',
            header: 'Nhân sự phụ trách',
            width: 210,
            minWidth: 140,
            compactHidden: true,
          },
        ]
      : []),
    ...(showStatus
      ? [
          {
            key: 'status',
            header: 'Trạng thái',
            width: 180,
            minWidth: 120,
            align: 'center' as const,
          },
        ]
      : []),
    {
      key: 'action',
      header: 'Thao tác',
      width: 92,
      minWidth: 60,
      hideable: false,
      align: 'center',
    },
  ], [showNstmColumns, showStatus])

  function patch(index: number, changes: Partial<SurveyRequestLine>) {
    onChange(lines.map((line, i) => (i === index ? { ...line, ...changes } : line)))
  }

  // bao-CR-289: chọn sản phẩm từ danh mục — YCBG không có cột tên riêng nên tên
  // sản phẩm chỉ điền vào Chi tiết thông số khi ô đó còn trống, không đè chữ đã gõ.
  function applyProduct(index: number, product: ProductOption | null) {
    if (!product) {
      patch(index, { product_code: '' })
      return
    }
    const current = lines[index]
    if (!current) return
    patch(index, {
      product_code: product.code,
      uom: product.unit || current.uom,
      item_group: product.item_group || current.item_group,
      requirement_detail: current.requirement_detail || product.name,
    })
  }

  // bao-CR-289: áp lịch sử mua gần nhất của mã hàng — mirror YCMH nhưng đổ vào
  // bộ trường của dòng YCBG (SL dự kiến / giá đề xuất).
  function applyPurchaseHistory(index: number, history: PurchaseHistoryRow) {
    const current = lines[index]
    if (!current) return

    const vat = Number(history.vat)
    const previousWarehouse = history.extra?.warehouse_code?.trim() || ''
    const warehouse = previousWarehouse
      ? warehouses.data?.items.find(
          (option) =>
            option.code === previousWarehouse || option.name === previousWarehouse,
        )?.name || current.warehouse
      : current.warehouse

    patch(index, {
      uom: history.unit || current.uom,
      request_qty: Number(history.qty_order) || 0,
      proposed_price: Number(history.price) || 0,
      vat_pct: VAT_OPTIONS.some((option) => option === vat) ? vat : current.vat_pct,
      item_group: history.extra?.item_group?.trim() || current.item_group,
      warehouse,
    })
    toast.success('Đã áp dụng dữ liệu từ lịch sử — bấm Lưu để ghi nhận')
  }

  // Đang sửa thì tính sống theo SL × giá × VAT để người gõ thấy ngay số đổi.
  const lineTotal = (line: SurveyRequestLine) =>
    line.request_qty * line.proposed_price * (1 + (line.vat_pct || 0) / 100)

  function duplicate(index: number) {
    const source = lines[index]
    if (!source) return
    const copy: SurveyRequestLine = {
      ...source,
      id: 0,
      received_date: '',
      result_date: '',
      assignee: '',
      assignee_name: '',
      pr_id: 0,
      pr_code: '',
      po_id: 0,
      po_code: '',
      is_completed: false,
      line_status: '',
      no_option: false,
      option_count: 0,
      has_chosen: false,
      progress_state: '',
      progress_tone: 'gray',
      // bao-CR-289: tiến độ là của dòng gốc, dòng nhân bản bắt đầu từ số 0.
      qty_ordered: 0,
      qty_received: 0,
      expected_date: '',
      progress_note: '',
    }
    onChange([...lines.slice(0, index + 1), copy, ...lines.slice(index + 1)])
    onLineDuplicated?.(index)
  }

  function remove(index: number) {
    onChange(lines.filter((_, i) => i !== index))
    onLineRemoved?.(index)
  }

  function renderCell(key: string, line: SurveyRequestLine, index: number) {
    switch (key) {
      case 'no':
        return <span className="text-muted-foreground">{index + 1}</span>

      case 'product_code':
        return (
          <div className="flex min-w-0 items-center gap-0.5">
            <div className="min-w-0 flex-1">
              {editing ? (
                <PurchaseRequestProductPicker
                  code={line.product_code}
                  name={line.requirement_detail}
                  onPick={(product) => applyProduct(index, product)}
                />
              ) : (
                <span
                  className="block break-words whitespace-normal leading-snug font-medium"
                  title={line.product_code}
                >
                  {line.product_code || '—'}
                </span>
              )}
            </div>
            {/* Đang sửa thì mã nằm trong ô chọn (một <button>) nên bôi đen không
                được — nút chép là đường duy nhất lấy được mã ra ngoài. */}
            <CopyButton value={line.product_code} label="mã hàng" className="size-7" />
            {!!line.product_code && (
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                className="size-7 shrink-0 text-muted-foreground"
                title="Xem lịch sử mua hàng gần nhất"
                aria-label={`Xem lịch sử mua hàng của ${line.product_code}`}
                onClick={() => setHistoryIndex(index)}
              >
                <History />
              </Button>
            )}
          </div>
        )

      case 'warehouse':
        return editing ? (
          <CatalogSelect
            value={line.warehouse}
            placeholder="-- Kho --"
            invalid={invalid?.has(`line-${index}-warehouse`)}
            options={(warehouses.data?.items ?? []).map((warehouse) => ({
              value: warehouse.name,
              label: warehouse.code
                ? `${warehouse.code} - ${warehouse.name}`
                : warehouse.name,
            }))}
            onChange={(value) => patch(index, { warehouse: value })}
          />
        ) : (
          <span className="block break-words whitespace-normal leading-snug" title={line.warehouse}>
            {line.warehouse || '—'}
          </span>
        )

      case 'vat':
        return editing ? (
          <Select
            value={String(line.vat_pct ?? 8)}
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
          <span className="tabular-nums">{line.vat_pct || 0}%</span>
        )

      case 'amount':
        return (
          <span className="tabular-nums font-semibold text-navy">
            {formatMoney(lineTotal(line))}
          </span>
        )

      case 'required_date':
        return editing ? (
          <DatePicker
            size="sm"
            value={line.required_date || ''}
            placeholder="Chọn ngày"
            className={cn(
              invalid?.has(`line-${index}-required_date`) &&
                'border-destructive ring-2 ring-destructive/20',
            )}
            onChange={(next) => patch(index, { required_date: next })}
          />
        ) : (
          <span className="tabular-nums">{formatDate(line.required_date) || '—'}</span>
        )

      case 'progress':
        return (
          <span className="tabular-nums">
            {formatQuantity(line.qty_received)} / {formatQuantity(line.qty_ordered)}
          </span>
        )

      case 'expected':
        // Chỉ hiển thị — NSTM sửa trong popup Chi tiết dòng (endpoint progress riêng).
        return (
          <span className="tabular-nums">{formatDate(line.expected_date) || '—'}</span>
        )

      case 'item_group':
        return editing ? (
          <CatalogSelect
            value={line.item_group}
            placeholder="-- Phân loại --"
            invalid={invalid?.has(`line-${index}-item_group`)}
            options={(itemGroups.data?.items ?? []).map((group) => ({
              value: group.name,
              label: group.name,
            }))}
            onChange={(value) => patch(index, { item_group: value })}
          />
        ) : (
          <span className="block break-words whitespace-normal leading-snug" title={line.item_group}>
            {line.item_group || '—'}
          </span>
        )

      case 'requirement_detail':
        //  Ô nhập phải là textarea TỰ GIÃN chứ không phải input một dòng: thông
        //  số dài hơn bề rộng cột là bị cắt mất phần đuôi ngay lúc đang gõ
        //  (lỗi QA 29/08 — "bảng thông tin bị ẩn nếu dài quá").
        return editing ? (
          <Textarea
            rows={1}
            className="min-h-9 resize-none py-1.5"
            value={line.requirement_detail}
            placeholder="Thông số / chất lượng cần khảo sát"
            onChange={(event) => patch(index, { requirement_detail: event.target.value })}
          />
        ) : (
          <span className="block break-words whitespace-normal font-medium leading-snug" title={line.requirement_detail}>
            {line.requirement_detail || '—'}
          </span>
        )

      case 'received_date':
        return (
          <span className="text-muted-foreground">
            {formatDate(line.received_date) || '—'}
          </span>
        )

      case 'result_due_date':
        return editing ? (
          <DatePicker
            size="sm"
            value={line.result_due_date || ''}
            onChange={(value) => patch(index, { result_due_date: value })}
          />
        ) : (
          formatDate(line.result_due_date) || '—'
        )

      case 'request_qty':
        return editing ? (
          <Input
            className={cn(
              'text-right',
              invalid?.has(`line-${index}-request_qty`) &&
                'border-destructive ring-2 ring-destructive/20',
            )}
            type="number"
            min={0}
            step="0.001"
            value={line.request_qty || ''}
            onChange={(event) => patch(index, { request_qty: Number(event.target.value) })}
          />
        ) : (
          <span className="tabular-nums">{formatQuantity(line.request_qty) || '—'}</span>
        )

      case 'uom':
        return editing ? (
          <CatalogSelect
            value={line.uom}
            placeholder="-- ĐVT --"
            options={(units.data?.items ?? []).map((unit) => ({
              value: unit.name,
              label: unit.name,
            }))}
            onChange={(value) => patch(index, { uom: value })}
          />
        ) : (
          line.uom || '—'
        )

      case 'proposed_price':
        return editing ? (
          <Input
            className="text-right"
            type="number"
            min={0}
            step="0.0001"
            value={line.proposed_price || ''}
            onChange={(event) =>
              patch(index, { proposed_price: Number(event.target.value) })
            }
          />
        ) : (
          <span className="tabular-nums">{formatUnitPrice(line.proposed_price) || '—'}</span>
        )

      case 'assignee':
        return canAssignNstm && line.id ? (
          <Select
            value={line.assignee || undefined}
            onValueChange={(value) => {
              const assignee = value === UNASSIGNED ? '' : value
              patch(index, { assignee })
              onAssigneeChange(line, assignee)
            }}
          >
            <SelectTrigger size="sm" className="w-full">
              <SelectValue placeholder="Chọn NSTM" />
            </SelectTrigger>
            <SelectContent>
              {line.assignee && (
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
            {line.assignee_name ||
              purchasers.find((purchaser) => purchaser.code === line.assignee)?.name ||
              line.assignee ||
              '—'}
          </span>
        )

      case 'status':
        return <SurveyLineStateBadge state={line.progress_state} tone={line.progress_tone} />

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
              <>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  title="Nhân bản dòng"
                  onClick={() => duplicate(index)}
                >
                  <Copy />
                </Button>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  className="text-destructive hover:text-destructive"
                  title="Xóa dòng"
                  onClick={() => remove(index)}
                >
                  <Trash2 />
                </Button>
              </>
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
        rows={lines}
        storageKey={TABLE_STORAGE_KEY}
        rowKey={(line, index) => line.id || `new-${index}`}
        renderCell={renderCell}
        title={`Danh sách sản phẩm (${lines.length} dòng)`}
        emptyMessage='Chưa có dòng nào — nhấn "Thêm dòng" để bắt đầu'
      />

      {/* bao-CR-289: lịch sử mua hàng của mã trên dòng — mirror YCMH. */}
      <PurchaseHistoryDialog
        open={historyIndex !== null}
        productCode={historyIndex === null ? '' : lines[historyIndex]?.product_code || ''}
        productName={historyIndex === null ? '' : lines[historyIndex]?.requirement_detail || ''}
        readOnly={!editing}
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

function CatalogSelect({
  value,
  placeholder,
  invalid = false,
  options,
  onChange,
}: {
  value: string
  placeholder: string
  /** Tô đỏ khi ô bị chặn lúc Gửi duyệt vì còn trống. */
  invalid?: boolean
  options: { value: string; label: string }[]
  onChange: (value: string) => void
}) {
  return (
    <Select
      value={value || EMPTY_CATALOG_VALUE}
      onValueChange={(next) => onChange(next === EMPTY_CATALOG_VALUE ? '' : next)}
    >
      <SelectTrigger
        size="sm"
        className={cn('w-full', invalid && 'border-destructive ring-2 ring-destructive/20')}
      >
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
