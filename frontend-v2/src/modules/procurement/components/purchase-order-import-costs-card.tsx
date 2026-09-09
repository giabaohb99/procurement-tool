import {
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Pencil,
  Plus,
  Receipt,
  Trash2,
} from 'lucide-react'
import { Fragment, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import type { Supplier } from '@/modules/production/types/supplier'
import { appRoutes } from '@/shared/constants/app-routes'
import { LinesTable } from '@/shared/data-table/lines-table'
import type { LinesTableColumn } from '@/shared/data-table/types'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { confirm as confirmDialog } from '@/shared/ui/confirm-dialog'
import { DatePicker } from '@/shared/ui/date-picker'
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { NumberInput, PRICE_MAX_DECIMALS } from '@/shared/ui/number-input'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { SearchSelect } from '@/shared/ui/search-select'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import {
  ALLOCATION_BY_PRODUCT,
  ALLOCATION_MANUAL,
  ALLOCATION_METHOD_OPTIONS,
  CURRENCY_OPTIONS,
  DEFAULT_CURRENCY,
  IMPORT_COST_TYPE_OPTIONS,
  MANUAL_ALLOCATION_TOLERANCE,
  PO_IMPORT_COST_PAYABLE_STATUSES,
  STATE_BUDGET_SUPPLIER_CODE,
  STATE_BUDGET_SUPPLIER_NAME,
  importCostTypeLabel,
  type ImportCostAllocationLine,
  type ImportCostAllocationShare,
  type PurchaseOrderDetail,
  type PurchaseOrderImportCost,
} from '../types/purchase-order-detail'
import { createEmptyImportCost } from '../utils/purchase-order-draft'
import {
  applyCostType,
  costBaseAmount,
  displayCostBaseAmount,
  displayLineBaseAmount,
  groupCostsBySupplier,
  groupCostsByType,
  isManualAllocation,
  manualAllocationGap,
  manualAllocationTotal,
  paymentBlockReason,
  percentOf,
  setManualAllocation,
  switchAllocationMethod,
} from '../utils/purchase-order-import-cost'

/**
 * Có hậu tố `-v2` vì khóa cũ `erp.table.purchase-order-import-costs` còn giữ bố cục
 * của bảng đời trước trong `localStorage`: `useTableLayout` ưu tiên bố cục đã lưu,
 * cột mới (chọn, mã hàng chỉ định, đã chi, còn lại, ghi chú) bị dồn xuống cuối nên
 * bảng nhìn lộn xộn. Đổi khóa để thứ tự mặc định bên dưới có hiệu lực; đổi bộ cột
 * lần sau thì tăng số phiên bản tiếp.
 */
const TABLE_STORAGE_KEY = 'purchase-order-import-costs-v2'

/** Giá trị ô chọn NCC khi khoản chưa gắn NCC nào (Radix Select không nhận chuỗi rỗng). */
const SUPPLIER_EMPTY = '__none__'
/** Giá trị ô "Mã hàng chỉ định" khi chưa chọn mã nào. */
const TARGET_EMPTY = '__none__'

const DESCRIPTION_PLACEHOLDER = 'VD: Cước biển Thượng Hải – Cát Lái'
const DIALOG_DESCRIPTION_PLACEHOLDER = 'VD: Cước biển Thượng Hải – Cát Lái, 1x20DC'

/**
 * Bảng khoản chi phí. Cột xếp theo thứ tự đọc của người nhập, thành từng cụm:
 * nhận diện khoản (#, loại, diễn giải, NCC) → tiền (tiền tệ, tỷ giá, số tiền,
 * VAT, quy đổi, đã chi, còn lại) → phân bổ → hóa đơn & hạn trả → ghi chú →
 * hành động. Ba cột đầu ghim trái để cuộn ngang vẫn biết đang xem khoản nào;
 * cụm hóa đơn và ghi chú xếp `compactHidden` nên bảng rút gọn chỉ còn xương sống.
 * Cột tick chỉ thêm vào khi đơn đã duyệt và người dùng lập được YCTT.
 */
const BASE_COLUMNS: LinesTableColumn[] = [
  { key: 'no', header: '#', width: 44, minWidth: 40, hideable: false, defaultPinned: true, align: 'center' },
  {
    key: 'cost_type',
    header: 'Loại chi phí',
    width: 200,
    minWidth: 140,
    hideable: false,
    defaultPinned: true,
    wrap: true,
  },
  { key: 'description', header: 'Diễn giải', width: 300, minWidth: 160, wrap: true },
  { key: 'supplier', header: 'Nhà cung cấp', width: 230, minWidth: 150, wrap: true },
  { key: 'currency', header: 'Tiền tệ', width: 95, minWidth: 80, align: 'center' },
  { key: 'exchange_rate', header: 'Tỷ giá', width: 110, minWidth: 80, align: 'right' },
  { key: 'amount', header: 'Số tiền (trước thuế)', width: 145, minWidth: 100, align: 'right' },
  { key: 'vat', header: 'VAT%', width: 80, minWidth: 60, align: 'right' },
  { key: 'base_amount', header: 'Quy đổi (VNĐ)', width: 145, minWidth: 100, align: 'right' },
  { key: 'paid_amount', header: 'Đã chi', width: 120, minWidth: 90, align: 'right' },
  { key: 'remaining', header: 'Còn lại', width: 120, minWidth: 90, align: 'right' },
  { key: 'allocation_method', header: 'Cách phân bổ', width: 160, minWidth: 120 },
  { key: 'allocation_target', header: 'Mã hàng chỉ định', width: 155, minWidth: 110, wrap: true },
  { key: 'invoice_no', header: 'Số hóa đơn', width: 110, minWidth: 80, compactHidden: true },
  { key: 'invoice_date', header: 'Ngày hóa đơn', width: 130, minWidth: 110, compactHidden: true },
  { key: 'payment_due_date', header: 'Hạn thanh toán', width: 130, minWidth: 110, compactHidden: true },
  { key: 'note', header: 'Ghi chú', width: 150, minWidth: 100, wrap: true, compactHidden: true },
  { key: 'action', header: 'Hành động', width: 90, minWidth: 80, hideable: false, align: 'center' },
]

const TICK_COLUMN: LinesTableColumn = {
  key: 'tick',
  header: 'Chọn',
  // 60px: 44px vừa đủ ô tick nhưng tiêu đề "Chọn" bị cắt thành "Ch…" (khách báo 09/09).
  width: 60,
  minWidth: 52,
  hideable: false,
  defaultPinned: true,
  align: 'center',
}

/**
 * Ô chọn trong bảng: cho nhãn dài tự xuống dòng thay vì cắt cụt. Bản shadcn gốc
 * ghim `whitespace-nowrap` + `line-clamp-1` + chiều cao cứng nên "Phí địa phương
 * tại cảng" hiện thành "Phí địa phương tại cản…" (khách báo 09/09/2026).
 */
const WRAPPING_SELECT_TRIGGER =
  'h-auto min-h-9 w-full items-start py-1.5 text-left whitespace-normal data-[size=default]:h-auto *:data-[slot=select-value]:line-clamp-none'

interface SupplierOption {
  code: string
  name: string
}

interface PurchaseOrderImportCostsCardProps {
  order: PurchaseOrderDetail
  /** Bảng mở ô nhập: đơn nháp / bị trả, HOẶC đã duyệt mà còn quyền sửa (cước, thuế về sau). */
  editable: boolean
  /** Đơn chưa lưu lần nào — chưa có id dòng nên chưa chia nhập tay, chưa thành công nợ. */
  isNew: boolean
  /** Danh mục NCC để chọn người nhận tiền; thiếu quyền `supplier.read` thì rỗng. */
  suppliers: Supplier[]
  onChange: (costs: PurchaseOrderImportCost[]) => void
}

/**
 * bao-CR-319 — thẻ "Chi phí lô hàng nhập khẩu" trên chi tiết ĐMH, bê nguyên bố cục
 * bản v1 sang (khách yêu cầu 09/09/2026):
 *
 * 1. Bảng khoản chi phí (cột tick lập YCTT, bút mở popup chi tiết, thùng rác xóa).
 * 2. Năm ô số: tiền hàng · tổng chi phí · đã chi · còn phải chi · tổng giá trị lô.
 * 3. "Thanh toán chi phí theo nhà cung cấp" — mỗi YCTT chỉ một NCC.
 * 4. Gom theo loại chi phí (+ theo NCC khi chưa thành công nợ).
 * 5. "Chi phí theo dòng hàng" — bung từng dòng xem khoản nào chia bao nhiêu, và gõ
 *    số cho khoản "Nhập tay" ngay tại đây.
 *
 * Số của backend (`import_cost_summary`, `import_cost_allocation`) là nguồn sự thật;
 * đơn chưa lưu thì tính tạm bằng `purchase-order-import-cost.ts` để nhìn ngay.
 */
export function PurchaseOrderImportCostsCard({
  order,
  editable,
  isNew,
  suppliers,
  onChange,
}: PurchaseOrderImportCostsCardProps) {
  const navigate = useNavigate()
  const { can } = usePermission()
  // Giữ cùng một mảng giữa các lượt render khi đơn chưa có khoản nào — `?? []` tạo mảng
  // mới mỗi lần nên các useMemo bên dưới sẽ tính lại vô ích.
  const rawCosts = order.import_costs
  const costs = useMemo(() => rawCosts ?? [], [rawCosts])

  const [selectedPayableIds, setSelectedPayableIds] = useState<Set<number>>(() => new Set())
  const [detailIndex, setDetailIndex] = useState<number | null>(null)
  const [openLineIds, setOpenLineIds] = useState<Set<number>>(() => new Set())

  const approved = PO_IMPORT_COST_PAYABLE_STATUSES.includes(order.status)
  /** Đơn đã duyệt và người này lập được YCTT — bật cột tick + bảng thanh toán theo NCC. */
  const payReady = approved && can('payment_request', 'create')

  /** NCC của đơn có thể không thuộc danh mục (NSNN, mã cũ) — nối thêm để ô chọn hiện đúng. */
  const supplierOptions = useMemo<SupplierOption[]>(() => {
    const seen = new Set(suppliers.map((supplier) => supplier.code))
    const extra = costs
      .filter((cost) => cost.supplier_code && !seen.has(cost.supplier_code))
      .map((cost) => ({ code: cost.supplier_code, name: cost.supplier_name }))
    const unique = new Map<string, SupplierOption>()
    for (const supplier of [...suppliers, ...extra]) unique.set(supplier.code, supplier)
    if (!unique.has(STATE_BUDGET_SUPPLIER_CODE)) {
      unique.set(STATE_BUDGET_SUPPLIER_CODE, {
        code: STATE_BUDGET_SUPPLIER_CODE,
        name: STATE_BUDGET_SUPPLIER_NAME,
      })
    }
    return Array.from(unique.values())
  }, [suppliers, costs])

  const supplierSelectOptions = useMemo(
    () =>
      supplierOptions.map((supplier) => ({
        value: supplier.code,
        label: supplier.name ? `${supplier.code} — ${supplier.name}` : supplier.code,
      })),
    [supplierOptions],
  )

  const productCodes = useMemo(
    () =>
      Array.from(
        new Set(order.items.map((item) => item.product_code).filter((code) => code !== '')),
      ),
    [order.items],
  )

  const summary = order.import_cost_summary
  const allocation = order.import_cost_allocation
  const allocationLines = useMemo(() => allocation?.lines ?? [], [allocation])

  /** Khoản tick được: đã thành công nợ, còn phải chi. */
  const selectablePayableIds = useMemo(
    () =>
      costs
        .filter((cost) => cost.payable_id && paymentBlockReason(cost, approved) === null)
        .map((cost) => cost.payable_id ?? 0),
    [costs, approved],
  )
  const effectiveSelected = useMemo(
    () => selectablePayableIds.filter((id) => selectedPayableIds.has(id)),
    [selectablePayableIds, selectedPayableIds],
  )

  const columns = useMemo(() => (payReady ? [TICK_COLUMN, ...BASE_COLUMNS] : BASE_COLUMNS), [payReady])

  // ---- Số tổng: lấy của backend, đơn đang gõ dở thì tính tại chỗ để nhìn ngay ----
  const goodsBase = useMemo(() => {
    if (summary) return summary.goods_base_total
    return order.items.reduce((sum, item) => sum + displayLineBaseAmount(item, order), 0)
  }, [summary, order])
  const costTotal = useMemo(
    () => costs.reduce((sum, cost) => sum + displayCostBaseAmount(cost), 0),
    [costs],
  )
  const paidTotal = summary?.paid_total ?? 0
  const remainingTotal = Math.max(costTotal - paidTotal, 0)
  const landedTotal = goodsBase + costTotal

  const byType = useMemo(() => groupCostsByType(costs), [costs])
  const bySupplierDraft = useMemo(() => groupCostsBySupplier(costs), [costs])
  const bySupplierPayable = useMemo(() => summary?.by_supplier ?? [], [summary])
  /** Dòng tổng của bảng thanh toán theo NCC — cộng lại từ chính các dòng đang bày. */
  const payableTotals = useMemo(
    () =>
      bySupplierPayable.reduce(
        (sum, group) => ({
          count: sum.count + group.count,
          base: sum.base + group.base_amount,
          paid: sum.paid + group.paid_amount,
          remaining: sum.remaining + group.remaining,
        }),
        { count: 0, base: 0, paid: 0, remaining: 0 },
      ),
    [bySupplierPayable],
  )

  const manualCosts = useMemo(() => costs.filter((cost) => isManualAllocation(cost)), [costs])

  function updateCost(index: number, patch: Partial<PurchaseOrderImportCost>) {
    onChange(costs.map((cost, i) => (i === index ? { ...cost, ...patch } : cost)))
  }

  function replaceCost(index: number, next: PurchaseOrderImportCost) {
    onChange(costs.map((cost, i) => (i === index ? next : cost)))
  }

  function addCost() {
    onChange([...costs, createEmptyImportCost()])
  }

  async function removeCost(index: number) {
    const ok = await confirmDialog({
      title: 'Xóa dòng chi phí',
      message: 'Xóa dòng chi phí này?',
      confirmLabel: 'Xóa',
    })
    if (!ok) return
    onChange(costs.filter((_, i) => i !== index))
    if (detailIndex === index) setDetailIndex(null)
  }

  function changeAllocationMethod(index: number, method: number) {
    replaceCost(index, switchAllocationMethod(costs[index], method, allocationLines))
    // Chuyển sang nhập tay thì mở hết dòng hàng cho người dùng thấy ngay chỗ gõ số.
    if (method === ALLOCATION_MANUAL) {
      setOpenLineIds(new Set(allocationLines.map((line) => line.item_id)))
    }
  }

  function changeCurrency(index: number, currency: string) {
    updateCost(index, { currency, exchange_rate: currency === DEFAULT_CURRENCY ? 1 : 0 })
  }

  function changeSupplier(index: number, code: string) {
    const supplier = supplierOptions.find((option) => option.code === code)
    updateCost(index, { supplier_code: code, supplier_name: supplier?.name ?? '' })
  }

  /** Khoản đã thành công nợ và đã chi một phần thì khóa số tiền — sửa là lệch sổ. */
  function amountLocked(cost: PurchaseOrderImportCost): boolean {
    return (cost.paid_amount ?? 0) > 0.01
  }

  function toggleSelected(payableId: number, checked: boolean) {
    setSelectedPayableIds((current) => {
      const next = new Set(current)
      if (checked) next.add(payableId)
      else next.delete(payableId)
      return next
    })
  }

  function toggleSelectAll(checked: boolean) {
    setSelectedPayableIds(checked ? new Set(selectablePayableIds) : new Set())
  }

  function goCreatePaymentRequest(payableIds: number[]) {
    if (payableIds.length === 0) return
    navigate(`${appRoutes.finance.paymentRequestNew}?payables=${payableIds.join(',')}`)
  }

  function toggleLine(itemId: number) {
    setOpenLineIds((current) => {
      const next = new Set(current)
      if (next.has(itemId)) next.delete(itemId)
      else next.add(itemId)
      return next
    })
  }

  const allLinesOpen = allocationLines.length > 0 && openLineIds.size >= allocationLines.length

  function renderCell(key: string, cost: PurchaseOrderImportCost, index: number) {
    const currency = (cost.currency || DEFAULT_CURRENCY).toUpperCase()
    const isVnd = currency === DEFAULT_CURRENCY
    const hasPayable = Boolean(cost.payable_id)
    const base = displayCostBaseAmount(cost)

    switch (key) {
      case 'tick': {
        const reason = paymentBlockReason(cost, approved)
        // Khách 09/09/2026: ô không có gì thì để TRỐNG, đừng vẽ dấu gạch.
        if (reason !== null || !cost.payable_id) return null
        const payableId = cost.payable_id
        return (
          <Checkbox
            aria-label={`Chọn khoản ${index + 1} để lập YCTT`}
            checked={selectedPayableIds.has(payableId)}
            onCheckedChange={(checked) => toggleSelected(payableId, checked === true)}
          />
        )
      }
      case 'no':
        return <span className="text-muted-foreground">{index + 1}</span>
      case 'cost_type':
        return editable ? (
          <Select
            value={String(cost.cost_type)}
            onValueChange={(value) => replaceCost(index, applyCostType(cost, Number(value)))}
          >
            <SelectTrigger className={WRAPPING_SELECT_TRIGGER} aria-label="Loại chi phí">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {IMPORT_COST_TYPE_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={String(option.value)}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : (
          <span className="font-medium">{cost.cost_type_label || importCostTypeLabel(cost.cost_type)}</span>
        )
      case 'description':
        return editable ? (
          <Textarea
            className="min-h-9 py-1.5"
            value={cost.description}
            placeholder={DESCRIPTION_PLACEHOLDER}
            aria-label="Diễn giải"
            onChange={(event) => updateCost(index, { description: event.target.value })}
          />
        ) : (
          cost.description || null
        )
      case 'allocation_method':
        return editable ? (
          <Select
            value={String(cost.allocation_method)}
            onValueChange={(value) => changeAllocationMethod(index, Number(value))}
          >
            <SelectTrigger className={WRAPPING_SELECT_TRIGGER} aria-label="Cách phân bổ">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ALLOCATION_METHOD_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={String(option.value)}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : (
          cost.allocation_method_label || allocationMethodLabel(cost.allocation_method)
        )
      case 'allocation_target':
        return renderAllocationTarget(cost, index)
      case 'supplier':
        return editable ? (
          <SearchSelect
            value={cost.supplier_code || ''}
            onChange={(value) => changeSupplier(index, value === SUPPLIER_EMPTY ? '' : value)}
            options={supplierSelectOptions}
            placeholder="Chọn/tìm NCC…"
            searchPlaceholder="Gõ mã hoặc tên NCC"
            emptyMessage="Không có NCC khớp"
            clearable
            wrap
          />
        ) : cost.supplier_code ? (
          <span>
            <span className="font-medium">{cost.supplier_code}</span>
            {cost.supplier_name && <span className="text-muted-foreground"> — {cost.supplier_name}</span>}
          </span>
        ) : null
      case 'currency':
        return editable ? (
          <Select value={currency} onValueChange={(value) => changeCurrency(index, value)}>
            <SelectTrigger className="w-full" aria-label="Tiền tệ">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CURRENCY_OPTIONS.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : (
          currency
        )
      case 'exchange_rate':
        if (isVnd) return null
        return editable ? (
          <NumberInput
            className="px-2 text-right"
            aria-label="Tỷ giá"
            value={cost.exchange_rate}
            maxDecimals={6}
            onChange={(value) => updateCost(index, { exchange_rate: value })}
          />
        ) : (
          <span className="tabular-nums">{formatUnitPrice(cost.exchange_rate)}</span>
        )
      case 'amount':
        return editable && !amountLocked(cost) ? (
          <NumberInput
            className="px-2 text-right"
            aria-label="Số tiền trước thuế"
            value={cost.amount}
            maxDecimals={PRICE_MAX_DECIMALS}
            onChange={(value) => updateCost(index, { amount: value })}
          />
        ) : (
          <span
            className="tabular-nums"
            title={amountLocked(cost) ? 'Khoản đã chi một phần — không sửa số tiền' : undefined}
          >
            {formatUnitPrice(cost.amount)}
          </span>
        )
      case 'vat':
        return editable ? (
          <NumberInput
            className="px-2 text-right"
            aria-label="VAT %"
            value={cost.vat}
            max={100}
            maxDecimals={2}
            onChange={(value) => updateCost(index, { vat: value })}
          />
        ) : (
          <span className="tabular-nums">{formatUnitPrice(cost.vat)}</span>
        )
      case 'base_amount':
        return <span className="font-semibold tabular-nums">{formatMoney(base)} đ</span>
      case 'paid_amount':
        return hasPayable ? (
          <span className="font-medium text-success tabular-nums">{formatMoney(cost.paid_amount ?? 0)} đ</span>
        ) : null
      case 'remaining': {
        const remaining = hasPayable ? (cost.remaining ?? 0) : base
        return (
          <span
            className={cn(
              'font-medium tabular-nums',
              remaining > 0.01 ? 'text-destructive' : 'text-muted-foreground',
            )}
          >
            {formatMoney(remaining)} đ
          </span>
        )
      }
      case 'invoice_no':
        return editable ? (
          <Input
            value={cost.invoice_no}
            aria-label="Số hóa đơn"
            onChange={(event) => updateCost(index, { invoice_no: event.target.value })}
          />
        ) : (
          cost.invoice_no || null
        )
      case 'invoice_date':
        return editable ? (
          <DatePicker
            value={cost.invoice_date || ''}
            onChange={(value) => updateCost(index, { invoice_date: value })}
          />
        ) : (
          formatDate(cost.invoice_date) || null
        )
      case 'payment_due_date':
        return editable ? (
          <DatePicker
            value={cost.payment_due_date || ''}
            onChange={(value) => updateCost(index, { payment_due_date: value })}
          />
        ) : (
          formatDate(cost.payment_due_date) || null
        )
      case 'note':
        return editable ? (
          <Textarea
            className="min-h-9 py-1.5"
            value={cost.note}
            aria-label="Ghi chú"
            onChange={(event) => updateCost(index, { note: event.target.value })}
          />
        ) : (
          cost.note || null
        )
      case 'action':
        return (
          <div className="flex items-center justify-center gap-0.5">
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              title="Chi tiết khoản chi phí"
              aria-label={`Chi tiết khoản chi phí ${index + 1}`}
              onClick={() => setDetailIndex(index)}
            >
              <Pencil />
            </Button>
            {editable && !hasPayable && (
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                className="text-destructive hover:text-destructive"
                title="Xóa dòng chi phí"
                aria-label={`Xóa dòng chi phí ${index + 1}`}
                onClick={() => void removeCost(index)}
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

  function renderAllocationTarget(cost: PurchaseOrderImportCost, index: number) {
    if (isManualAllocation(cost)) {
      return (
        <span className="text-xs text-muted-foreground">
          {manualStatusText(cost, isNew || !cost.id)}
        </span>
      )
    }
    if (Number(cost.allocation_method) === ALLOCATION_BY_PRODUCT) {
      if (!editable) return cost.allocation_target || null
      return (
        <Select
          value={cost.allocation_target || TARGET_EMPTY}
          onValueChange={(value) =>
            updateCost(index, { allocation_target: value === TARGET_EMPTY ? '' : value })
          }
        >
          <SelectTrigger className={WRAPPING_SELECT_TRIGGER} aria-label="Mã hàng chỉ định">
            <SelectValue placeholder="Chọn mã hàng" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={TARGET_EMPTY}>Chưa chọn mã hàng</SelectItem>
            {productCodes.map((code) => (
              <SelectItem key={code} value={code}>
                {code}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )
    }
    return null
  }

  const detailCost = detailIndex !== null ? costs[detailIndex] : undefined

  return (
    <>
      <Card className="gap-4 py-4">
        <CardHeader className="min-h-9 flex flex-row items-center justify-between gap-3 border-b px-4 pb-3!">
          <CardTitle className="flex items-center gap-2 text-base text-navy dark:text-foreground">
            <Receipt className="size-4" />
            Chi phí lô hàng nhập khẩu
          </CardTitle>
          <div className="flex flex-wrap items-center justify-end gap-2">
            {payReady && selectablePayableIds.length > 0 && (
              <>
                <label className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Checkbox
                    checked={
                      effectiveSelected.length === 0
                        ? false
                        : effectiveSelected.length === selectablePayableIds.length
                          ? true
                          : 'indeterminate'
                    }
                    onCheckedChange={(checked) => toggleSelectAll(checked === true)}
                  />
                  Tick mọi dòng còn phải chi
                </label>
                <Button
                  type="button"
                  size="sm"
                  disabled={effectiveSelected.length === 0}
                  onClick={() => goCreatePaymentRequest(effectiveSelected)}
                >
                  Tạo YCTT ({effectiveSelected.length} dòng đã tick)
                </Button>
              </>
            )}
            {editable && (
              <Button type="button" variant="outline" size="sm" onClick={addCost}>
                <Plus />
                Thêm chi phí
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4 px-4">
          <p className="rounded-md border border-info/30 bg-info/8 px-3 py-2 text-sm text-muted-foreground">
            VAT ở dòng hàng của đơn nhập khẩu luôn bằng 0 — thuế GTGT hàng nhập nộp ngân sách nhà
            nước theo tờ khai, khai thành một dòng ở bảng này. Chi phí vẫn thêm/sửa được sau khi
            đơn đã duyệt (hóa đơn cước, tờ khai thuế, phí lưu bãi đều có sau).
          </p>

          <LinesTable
            columns={columns}
            rows={costs}
            storageKey={TABLE_STORAGE_KEY}
            rowKey={(cost, index) => cost.id ?? `new-${index}`}
            renderCell={renderCell}
            title={<span className="text-sm font-medium">Khoản chi phí</span>}
            emptyMessage="Chưa khai chi phí nào cho lô hàng này"
            defaultCompact
            cellClassName={(key) => (key === 'base_amount' ? 'bg-warning/8' : undefined)}
          />

          <div className="grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(190px,1fr))]">
            <StatCard label="Tiền hàng (quy đổi)" value={goodsBase} tone="navy" />
            <StatCard
              label="Tổng chi phí nhập khẩu"
              value={costTotal}
              tone="amber"
              hint={`${percentOf(costTotal, goodsBase).toFixed(1)}% tiền hàng`}
            />
            {(payReady || paidTotal > 0) && (
              <>
                <StatCard
                  label="Đã chi"
                  value={paidTotal}
                  tone="success"
                  hint={`${percentOf(paidTotal, costTotal).toFixed(1)}% chi phí`}
                />
                <StatCard
                  label="Còn phải chi"
                  value={remainingTotal}
                  tone="destructive"
                  hint={`${percentOf(remainingTotal, costTotal).toFixed(1)}% chi phí`}
                />
              </>
            )}
            <StatCard label="Tổng giá trị lô hàng" value={landedTotal} tone="teal" />
          </div>

          {/*
            Hai cụm tổng đứng CẠNH nhau trên màn rộng: bảng thanh toán theo NCC bên
            trái, gom theo loại / theo NCC bên phải. Trước đây bảng chiếm hết bề ngang
            nên các cột số dạt về hai mép, còn cụm "Theo loại chi phí" trôi lơ lửng
            một mình dưới cùng — khách báo 09/09/2026 là nhìn "lệt lệt".
          */}
          <div className="grid items-start gap-3 xl:grid-cols-[minmax(0,1.6fr)_minmax(320px,1fr)]">
            {payReady && bySupplierPayable.length > 0 && (
            <div className="overflow-hidden rounded-md border">
              <div className="border-b bg-muted/40 px-3 py-2">
                <h4 className="text-sm font-semibold">Thanh toán chi phí theo nhà cung cấp</h4>
                <p className="text-xs text-muted-foreground">
                  Mỗi yêu cầu thanh toán chỉ một nhà cung cấp — bấm nút ở dòng NCC để lập phiếu cho
                  các khoản còn phải chi của NCC đó.
                </p>
              </div>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      {/* `w-full` cho cột NCC nuốt hết chỗ thừa, các cột số bám sát nhau. */}
                      <TableHead className="w-full">Nhà cung cấp</TableHead>
                      <TableHead className="w-[64px] text-center whitespace-nowrap">Số khoản</TableHead>
                      <TableHead className="w-[120px] text-right whitespace-nowrap">Phải trả</TableHead>
                      <TableHead className="w-[110px] text-right whitespace-nowrap">Đã chi</TableHead>
                      <TableHead className="w-[120px] text-right whitespace-nowrap">Còn lại</TableHead>
                      <TableHead className="w-[104px] text-right" />
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {bySupplierPayable.map((group) => {
                      const settled = group.remaining <= 0.01
                      return (
                        <TableRow key={group.supplier_code || '__empty__'}>
                          <TableCell>
                            {group.supplier_code ? (
                              <>
                                <span className="font-medium">{group.supplier_code}</span>
                                {group.supplier_name && (
                                  <span className="text-muted-foreground"> — {group.supplier_name}</span>
                                )}
                              </>
                            ) : (
                              <span className="text-muted-foreground">
                                (chưa chọn NCC — chưa thành công nợ)
                              </span>
                            )}
                          </TableCell>
                          <TableCell className="text-center tabular-nums">{group.count}</TableCell>
                          <TableCell className="text-right tabular-nums">
                            {formatMoney(group.base_amount)} đ
                          </TableCell>
                          <TableCell className="text-right text-success tabular-nums">
                            {formatMoney(group.paid_amount)} đ
                          </TableCell>
                          <TableCell
                            className={cn(
                              'text-right font-semibold tabular-nums',
                              settled ? 'text-muted-foreground' : 'text-destructive',
                            )}
                          >
                            {formatMoney(group.remaining)} đ
                          </TableCell>
                          <TableCell className="text-right">
                            {settled ? (
                              <Badge variant="outline">Đã chi đủ</Badge>
                            ) : (
                              <Button
                                type="button"
                                size="sm"
                                variant="outline"
                                disabled={group.unpaid_payable_ids.length === 0}
                                onClick={() => goCreatePaymentRequest(group.unpaid_payable_ids)}
                              >
                                Tạo YCTT
                              </Button>
                            )}
                          </TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                  <TableFooter>
                    <TableRow>
                      <TableCell className="font-semibold">Tổng cộng</TableCell>
                      <TableCell className="text-center tabular-nums">
                        {payableTotals.count}
                      </TableCell>
                      <TableCell className="text-right font-semibold tabular-nums">
                        {formatMoney(payableTotals.base)} đ
                      </TableCell>
                      <TableCell className="text-right font-semibold text-success tabular-nums">
                        {formatMoney(payableTotals.paid)} đ
                      </TableCell>
                      <TableCell
                        className={cn(
                          'text-right font-semibold tabular-nums',
                          payableTotals.remaining > 0.01 ? 'text-destructive' : 'text-muted-foreground',
                        )}
                      >
                        {formatMoney(payableTotals.remaining)} đ
                      </TableCell>
                      <TableCell />
                    </TableRow>
                  </TableFooter>
                </Table>
              </div>
            </div>
            )}

            {costs.length > 0 && (
              <div className="space-y-3">
                <SummaryBlock
                  title="Theo loại chi phí"
                  rows={byType.map((group) => ({
                    key: String(group.cost_type),
                    label: `${group.label} (${group.count})`,
                    value: group.base_amount,
                  }))}
                  total={costTotal}
                />
                {!payReady && (
                  <SummaryBlock
                    title="Theo nhà cung cấp"
                    rows={bySupplierDraft.map((group) => ({
                      key: group.supplier_code || '__empty__',
                      label: `${group.supplier_code ? `${group.supplier_code} — ${group.supplier_name}` : '(chưa chọn NCC)'} (${group.count})`,
                      value: group.base_amount,
                    }))}
                    total={costTotal}
                  />
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {!isNew && allocation && (
        <Card className="gap-4 py-4">
          <CardHeader className="min-h-9 flex flex-row items-center justify-between gap-3 border-b px-4 pb-3!">
            <div className="min-w-0 space-y-0.5">
              <CardTitle className="text-base text-navy dark:text-foreground">
                Chi phí theo dòng hàng
              </CardTitle>
              <p className="text-xs text-muted-foreground">
                Số chia lấy từ dữ liệu đã lưu, không ghi vào kho. Khoản chọn &quot;Nhập tay&quot;
                thì gõ số tiền từng dòng ở đây; sửa xong bấm Lưu mới có hiệu lực.
              </p>
            </div>
            {allocationLines.length > 0 && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() =>
                  setOpenLineIds(
                    allLinesOpen ? new Set() : new Set(allocationLines.map((line) => line.item_id)),
                  )
                }
              >
                {allLinesOpen ? 'Thu gọn' : 'Mở tất cả'}
              </Button>
            )}
          </CardHeader>
          <CardContent className="space-y-3 px-4">
            {manualCosts.map((cost) => (
              <ManualAllocationBanner key={cost.id ?? cost.description} cost={cost} />
            ))}

            {allocation.warnings.length > 0 && (
              <div className="flex items-start gap-2 rounded-md border border-warning/40 bg-warning/8 px-3 py-2 text-sm">
                <AlertTriangle className="mt-0.5 size-4 shrink-0 text-warning" />
                <ul className="list-disc space-y-0.5 pl-4">
                  {allocation.warnings.map((warning) => (
                    <li key={warning}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="overflow-x-auto rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-8" />
                    <TableHead>Mã hàng</TableHead>
                    <TableHead>Tên hàng</TableHead>
                    <TableHead className="text-right">SL đặt</TableHead>
                    <TableHead className="text-right">KL (kg)</TableHead>
                    <TableHead className="text-right">Tiền hàng (quy đổi)</TableHead>
                    <TableHead className="text-right">Chi phí phân bổ</TableHead>
                    <TableHead className="text-right">Tổng giá trị</TableHead>
                    <TableHead className="text-right">Tỷ lệ chi phí</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {allocationLines.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center text-muted-foreground">
                        Đơn chưa có dòng hàng
                      </TableCell>
                    </TableRow>
                  )}
                  {allocationLines.map((line) => {
                    const open = openLineIds.has(line.item_id)
                    return (
                      <Fragment key={line.item_id}>
                        <TableRow
                          className="cursor-pointer"
                          onClick={() => toggleLine(line.item_id)}
                        >
                          <TableCell className="text-muted-foreground">
                            {open ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}
                          </TableCell>
                          <TableCell className="font-medium">{line.product_code}</TableCell>
                          <TableCell>{line.product_name}</TableCell>
                          <TableCell className="text-right tabular-nums">
                            {formatQuantity(line.qty_order)}
                            {line.unit && <span className="text-muted-foreground"> {line.unit}</span>}
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {line.weight_kg ? formatQuantity(line.weight_kg) : ''}
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {formatMoney(line.goods_base)} đ
                          </TableCell>
                          <TableCell className="text-right font-semibold text-amber-600 tabular-nums dark:text-amber-500">
                            {formatMoney(line.cost_base)} đ
                          </TableCell>
                          <TableCell className="text-right font-semibold tabular-nums">
                            {formatMoney(line.landed_base)} đ
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {line.goods_base > 0 ? `${percentOf(line.cost_base, line.goods_base).toFixed(1)}%` : '-'}
                          </TableCell>
                        </TableRow>
                        {open && (
                          <TableRow className="hover:bg-transparent">
                            <TableCell colSpan={9} className="bg-muted/40 p-3">
                              <AllocationLineDetail
                                line={line}
                                costs={costs}
                                editable={editable}
                                onReplaceCost={replaceCost}
                              />
                            </TableCell>
                          </TableRow>
                        )}
                      </Fragment>
                    )
                  })}
                </TableBody>
                {allocationLines.length > 0 && (
                  <TableFooter>
                    <TableRow>
                      <TableCell colSpan={5} className="font-semibold">
                        Tổng toàn đơn
                      </TableCell>
                      <TableCell className="text-right font-semibold tabular-nums">
                        {formatMoney(allocation.goods_base_total)} đ
                      </TableCell>
                      <TableCell className="text-right font-semibold text-amber-600 tabular-nums dark:text-amber-500">
                        {formatMoney(allocation.cost_total)} đ
                      </TableCell>
                      <TableCell className="text-right font-semibold text-teal-600 tabular-nums dark:text-teal-400">
                        {formatMoney(allocation.landed_total)} đ
                      </TableCell>
                      <TableCell className="text-right font-semibold tabular-nums">
                        {allocation.goods_base_total > 0
                          ? `${percentOf(allocation.cost_total, allocation.goods_base_total).toFixed(1)}%`
                          : '-'}
                      </TableCell>
                    </TableRow>
                  </TableFooter>
                )}
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {detailCost && detailIndex !== null && (
        <CostDetailDialog
          cost={detailCost}
          index={detailIndex}
          editable={editable}
          isNew={isNew}
          payReady={payReady}
          supplierOptions={supplierSelectOptions}
          productCodes={productCodes}
          onPatch={(patch) => updateCost(detailIndex, patch)}
          onReplace={(next) => replaceCost(detailIndex, next)}
          onChangeAllocationMethod={(method) => changeAllocationMethod(detailIndex, method)}
          onChangeCurrency={(currency) => changeCurrency(detailIndex, currency)}
          onChangeSupplier={(code) => changeSupplier(detailIndex, code)}
          onClose={() => setDetailIndex(null)}
        />
      )}
    </>
  )
}

// ---------------------------------------------------------------------------
// Chữ dùng chung
// ---------------------------------------------------------------------------

function allocationMethodLabel(method: number): string {
  return ALLOCATION_METHOD_OPTIONS.find((option) => option.value === Number(method))?.label ?? ''
}

/** Câu trạng thái cho ô "Mã hàng chỉ định" khi khoản chọn Nhập tay. */
function manualStatusText(cost: PurchaseOrderImportCost, unsaved: boolean): string {
  if (unsaved) return 'Lưu đơn trước rồi gõ số ở bảng Chi phí theo dòng hàng'
  const entered = manualAllocationTotal(cost)
  if (entered <= 0) return 'Gõ số ở bảng Chi phí theo dòng hàng'
  const gap = manualAllocationGap(cost)
  return gap === 0 ? 'Đã khớp tổng' : `Lệch ${formatMoney(Math.abs(gap))} đ`
}

// ---------------------------------------------------------------------------
// Ô số tổng
// ---------------------------------------------------------------------------

type StatTone = 'navy' | 'amber' | 'success' | 'destructive' | 'teal'

const STAT_TONE_CLASS: Record<StatTone, string> = {
  navy: 'text-navy dark:text-foreground',
  amber: 'text-amber-600 dark:text-amber-500',
  success: 'text-success',
  destructive: 'text-destructive',
  teal: 'text-teal-600 dark:text-teal-400',
}

function StatCard({
  label,
  value,
  tone,
  hint,
}: {
  label: string
  value: number
  tone: StatTone
  hint?: string
}) {
  return (
    <div className="rounded-lg border bg-muted/40 px-3 py-2.5">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className={cn('text-lg font-bold tabular-nums', STAT_TONE_CLASS[tone])}>
        {formatMoney(value)} đ
      </div>
      {hint && <div className="text-[11.5px] text-muted-foreground">{hint}</div>}
    </div>
  )
}

function SummaryBlock({
  title,
  rows,
  total,
}: {
  title: string
  rows: { key: string; label: string; value: number }[]
  /** Dòng tổng dưới cùng — để cụm không cụt lủn khi đứng cạnh bảng bên trái. */
  total?: number
}) {
  return (
    <div className="w-full overflow-hidden rounded-md border">
      <div className="border-b bg-muted/40 px-3 py-2 text-sm font-semibold">{title}</div>
      <dl className="divide-y">
        {rows.map((row) => (
          <div key={row.key} className="flex items-start justify-between gap-3 px-3 py-1.5 text-sm">
            {/* Nhãn dài (tên NCC) xuống dòng thay vì cắt cụt — khách báo 09/09/2026. */}
            <dt className="min-w-0 text-muted-foreground">{row.label}</dt>
            <dd className="shrink-0 font-medium tabular-nums">{formatMoney(row.value)} đ</dd>
          </div>
        ))}
      </dl>
      {total !== undefined && (
        <div className="flex items-center justify-between gap-3 border-t bg-muted/40 px-3 py-2 text-sm font-semibold">
          <span>Tổng cộng</span>
          <span className="tabular-nums">{formatMoney(total)} đ</span>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Chi phí theo dòng hàng
// ---------------------------------------------------------------------------

function ManualAllocationBanner({ cost }: { cost: PurchaseOrderImportCost }) {
  const entered = manualAllocationTotal(cost)
  const target = costBaseAmount(cost)
  const gap = manualAllocationGap(cost)
  const name = cost.description || cost.cost_type_label || importCostTypeLabel(cost.cost_type)
  const matched = entered > 0 && gap === 0
  const suffix =
    entered <= 0
      ? ' — chưa nhập số tiền dòng nào'
      : matched
        ? ' — đã khớp tổng'
        : ` — lệch ${formatMoney(Math.abs(gap))} đ, phải bằng nhau mới Lưu được`
  return (
    <div
      className={cn(
        'rounded-md border px-3 py-2 text-sm',
        matched
          ? 'border-success/40 bg-success/8 text-success'
          : 'border-destructive/40 bg-destructive/8 text-destructive',
      )}
    >
      Nhập tay khoản &quot;{name}&quot;: đã nhập {formatMoney(entered)} / {formatMoney(target)} đ
      {suffix}
    </div>
  )
}

function shareMethodLabel(share: ImportCostAllocationShare) {
  if (share.effective_method === share.allocation_method) return share.effective_method_label
  return (
    <span className="text-amber-700 dark:text-amber-500">
      {share.effective_method_label} (chọn {share.allocation_method_label.toLowerCase()}, thiếu cơ sở)
    </span>
  )
}

function AllocationLineDetail({
  line,
  costs,
  editable,
  onReplaceCost,
}: {
  line: ImportCostAllocationLine
  costs: PurchaseOrderImportCost[]
  editable: boolean
  onReplaceCost: (index: number, next: PurchaseOrderImportCost) => void
}) {
  const manualEntries = costs
    .map((cost, index) => ({ cost, index }))
    .filter(({ cost }) => isManualAllocation(cost) && cost.id)
  const manualIds = new Set(manualEntries.map(({ cost }) => cost.id))
  // Khoản nhập tay vẽ bằng ô nhập bên dưới — bỏ bản backend đã chia kẻo hiện hai lần.
  const shares = line.costs.filter((share) => !manualIds.has(share.cost_id))

  if (shares.length === 0 && manualEntries.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">Dòng này không được phân bổ khoản chi phí nào.</p>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Loại chi phí</TableHead>
          <TableHead>Diễn giải</TableHead>
          <TableHead>Nhà cung cấp</TableHead>
          <TableHead>Cách chia</TableHead>
          <TableHead className="text-right">Tỷ lệ</TableHead>
          <TableHead className="w-[160px] text-right">Số tiền (đ)</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {shares.map((share) => (
          <TableRow key={share.cost_id}>
            <TableCell className="font-medium">{share.cost_type_label}</TableCell>
            <TableCell>{share.description || ''}</TableCell>
            <TableCell>
              {share.supplier_code
                ? `${share.supplier_code}${share.supplier_name ? ` — ${share.supplier_name}` : ''}`
                : ''}
            </TableCell>
            <TableCell>{shareMethodLabel(share)}</TableCell>
            <TableCell className="text-right tabular-nums">{(share.ratio * 100).toFixed(2)}%</TableCell>
            <TableCell className="text-right font-medium tabular-nums">
              {formatMoney(share.base_amount)}
            </TableCell>
          </TableRow>
        ))}
        {manualEntries.map(({ cost, index }) => {
          const value = Number(cost.manual_allocation?.[String(line.item_id)] ?? 0)
          return (
            <TableRow key={`manual-${cost.id}`} className="bg-warning/8 hover:bg-warning/12">
              <TableCell className="font-medium">
                {cost.cost_type_label || importCostTypeLabel(cost.cost_type)}
              </TableCell>
              <TableCell>{cost.description || ''}</TableCell>
              <TableCell>
                {cost.supplier_code
                  ? `${cost.supplier_code}${cost.supplier_name ? ` — ${cost.supplier_name}` : ''}`
                  : ''}
              </TableCell>
              <TableCell>Nhập tay</TableCell>
              <TableCell className="text-right tabular-nums">
                {percentOf(value, costBaseAmount(cost)).toFixed(2)}%
              </TableCell>
              <TableCell className="text-right" onClick={(event) => event.stopPropagation()}>
                <NumberInput
                  className="px-2 text-right"
                  aria-label={`Số tiền nhập tay dòng ${line.product_code}`}
                  value={value}
                  disabled={!editable}
                  onChange={(next) => onReplaceCost(index, setManualAllocation(cost, line.item_id, next))}
                />
              </TableCell>
            </TableRow>
          )
        })}
      </TableBody>
    </Table>
  )
}

// ---------------------------------------------------------------------------
// Popup chi tiết một khoản (bút chì)
// ---------------------------------------------------------------------------

function Field({
  label,
  children,
  className,
}: {
  label: string
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={cn('space-y-1.5', className)}>
      <Label className="text-muted-foreground">{label}</Label>
      {children}
    </div>
  )
}

function CostDetailDialog({
  cost,
  index,
  editable,
  isNew,
  payReady,
  supplierOptions,
  productCodes,
  onPatch,
  onReplace,
  onChangeAllocationMethod,
  onChangeCurrency,
  onChangeSupplier,
  onClose,
}: {
  cost: PurchaseOrderImportCost
  index: number
  editable: boolean
  isNew: boolean
  payReady: boolean
  supplierOptions: { value: string; label: string }[]
  productCodes: string[]
  onPatch: (patch: Partial<PurchaseOrderImportCost>) => void
  onReplace: (next: PurchaseOrderImportCost) => void
  onChangeAllocationMethod: (method: number) => void
  onChangeCurrency: (currency: string) => void
  onChangeSupplier: (code: string) => void
  onClose: () => void
}) {
  const currency = (cost.currency || DEFAULT_CURRENCY).toUpperCase()
  const isVnd = currency === DEFAULT_CURRENCY
  const base = displayCostBaseAmount(cost)
  const hasPayable = Boolean(cost.payable_id)
  const amountLocked = (cost.paid_amount ?? 0) > 0.01
  const typeLabel = cost.cost_type_label || importCostTypeLabel(cost.cost_type)

  const payableNote = hasPayable
    ? ` · Đã chi ${formatMoney(cost.paid_amount ?? 0)} đ · Còn lại ${formatMoney(cost.remaining ?? 0)} đ`
    : ` · Chưa thành công nợ${
        isNew || !cost.id
          ? ' (dòng mới, Lưu đơn trước)'
          : payReady
            ? ' (chưa chọn NCC hoặc số tiền 0)'
            : ' (đơn chưa duyệt)'
      }`

  const supplierLabel =
    supplierOptions.find((option) => option.value === cost.supplier_code)?.label ||
    cost.supplier_code ||
    ''

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      {/* `max-w-*!`: `DialogContent` của shadcn có sẵn `sm:max-w-lg` — không đánh
          important thì hộp bị bóp lại, lưới 3 cột không còn chỗ (giống line-dialog). */}
      <DialogContent className="max-h-[92vh] w-[96vw] max-w-[860px]! overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            Chi tiết chi phí #{index + 1}: {typeLabel}
          </DialogTitle>
          <DialogDescription>
            Quy đổi {formatMoney(base)} đ{payableNote}
          </DialogDescription>
        </DialogHeader>

        <section className="space-y-3">
          <h4 className="text-sm font-semibold text-navy dark:text-foreground">Khoản chi phí</h4>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Field label="Loại chi phí">
              {editable ? (
                <Select
                  value={String(cost.cost_type)}
                  onValueChange={(value) => onReplace(applyCostType(cost, Number(value)))}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {IMPORT_COST_TYPE_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={String(option.value)}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <ReadOnlyValue>{typeLabel}</ReadOnlyValue>
              )}
            </Field>
            <Field label="Nhà cung cấp" className="lg:col-span-2">
              {editable ? (
                <SearchSelect
                  value={cost.supplier_code || ''}
                  onChange={(value) => onChangeSupplier(value === SUPPLIER_EMPTY ? '' : value)}
                  options={supplierOptions}
                  placeholder="Chọn/tìm NCC…"
                  searchPlaceholder="Gõ mã hoặc tên NCC"
                  emptyMessage="Không có NCC khớp"
                  clearable
                  wrap
                />
              ) : (
                <ReadOnlyValue>{supplierLabel}</ReadOnlyValue>
              )}
            </Field>
            <Field label="Diễn giải" className="sm:col-span-2 lg:col-span-3">
              {editable ? (
                <Textarea
                  value={cost.description}
                  placeholder={DIALOG_DESCRIPTION_PLACEHOLDER}
                  onChange={(event) => onPatch({ description: event.target.value })}
                />
              ) : (
                <ReadOnlyValue multiline>{cost.description || '—'}</ReadOnlyValue>
              )}
            </Field>
            <Field label="Tiền tệ">
              {editable ? (
                <Select value={currency} onValueChange={onChangeCurrency}>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CURRENCY_OPTIONS.map((option) => (
                      <SelectItem key={option} value={option}>
                        {option}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <ReadOnlyValue>{currency}</ReadOnlyValue>
              )}
            </Field>
            <Field label="Tỷ giá">
              {editable && !isVnd ? (
                <NumberInput
                  className="text-right"
                  value={cost.exchange_rate}
                  maxDecimals={6}
                  onChange={(value) => onPatch({ exchange_rate: value })}
                />
              ) : (
                <ReadOnlyValue className="tabular-nums">
                  {isVnd ? '1' : formatUnitPrice(cost.exchange_rate)}
                </ReadOnlyValue>
              )}
            </Field>
            <Field label={`Số tiền (trước thuế, ${currency})`}>
              {editable && !amountLocked ? (
                <NumberInput
                  className="text-right"
                  value={cost.amount}
                  maxDecimals={PRICE_MAX_DECIMALS}
                  onChange={(value) => onPatch({ amount: value })}
                />
              ) : (
                <ReadOnlyValue className="tabular-nums">{formatUnitPrice(cost.amount)}</ReadOnlyValue>
              )}
            </Field>
            <Field label="VAT %">
              {editable ? (
                <NumberInput
                  className="text-right"
                  value={cost.vat}
                  max={100}
                  maxDecimals={2}
                  onChange={(value) => onPatch({ vat: value })}
                />
              ) : (
                <ReadOnlyValue className="tabular-nums">{formatUnitPrice(cost.vat)}</ReadOnlyValue>
              )}
            </Field>
            <Field label="Quy đổi (VNĐ, đã gồm VAT)">
              <ReadOnlyValue className="font-semibold tabular-nums">{formatMoney(base)} đ</ReadOnlyValue>
            </Field>
            <Field label="Cách phân bổ">
              {editable ? (
                <Select
                  value={String(cost.allocation_method)}
                  onValueChange={(value) => onChangeAllocationMethod(Number(value))}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ALLOCATION_METHOD_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={String(option.value)}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <ReadOnlyValue>
                  {cost.allocation_method_label || allocationMethodLabel(cost.allocation_method)}
                </ReadOnlyValue>
              )}
            </Field>
            {Number(cost.allocation_method) === ALLOCATION_BY_PRODUCT && (
              <Field label="Mã hàng chỉ định">
                {editable ? (
                  <Select
                    value={cost.allocation_target || TARGET_EMPTY}
                    onValueChange={(value) =>
                      onPatch({ allocation_target: value === TARGET_EMPTY ? '' : value })
                    }
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="— chọn mã hàng —" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={TARGET_EMPTY}>— chọn mã hàng —</SelectItem>
                      {productCodes.map((code) => (
                        <SelectItem key={code} value={code}>
                          {code}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <ReadOnlyValue>{cost.allocation_target || '—'}</ReadOnlyValue>
                )}
              </Field>
            )}
            {isManualAllocation(cost) && (
              <Field label="Nhập tay">
                <ReadOnlyValue>{manualDialogStatus(cost)}</ReadOnlyValue>
              </Field>
            )}
          </div>
        </section>

        <section className="space-y-3">
          <h4 className="text-sm font-semibold text-navy dark:text-foreground">
            Hóa đơn và thanh toán
          </h4>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Field label="Số hóa đơn">
              {editable ? (
                <Input
                  value={cost.invoice_no}
                  onChange={(event) => onPatch({ invoice_no: event.target.value })}
                />
              ) : (
                <ReadOnlyValue>{cost.invoice_no || '—'}</ReadOnlyValue>
              )}
            </Field>
            <Field label="Ngày hóa đơn">
              {editable ? (
                <DatePicker
                  value={cost.invoice_date || ''}
                  onChange={(value) => onPatch({ invoice_date: value })}
                />
              ) : (
                <ReadOnlyValue>{formatDate(cost.invoice_date) || '—'}</ReadOnlyValue>
              )}
            </Field>
            <Field label="Hạn thanh toán">
              {editable ? (
                <DatePicker
                  value={cost.payment_due_date || ''}
                  onChange={(value) => onPatch({ payment_due_date: value })}
                />
              ) : (
                <ReadOnlyValue>{formatDate(cost.payment_due_date) || '—'}</ReadOnlyValue>
              )}
            </Field>
            {hasPayable && (
              <Field label="Công nợ">
                <ReadOnlyValue className="tabular-nums">
                  Đã chi {formatMoney(cost.paid_amount ?? 0)} đ · Còn lại{' '}
                  {formatMoney(cost.remaining ?? 0)} đ
                </ReadOnlyValue>
              </Field>
            )}
            <Field label="Ghi chú" className="sm:col-span-2 lg:col-span-3">
              {editable ? (
                <Textarea value={cost.note} onChange={(event) => onPatch({ note: event.target.value })} />
              ) : (
                <ReadOnlyValue multiline>{cost.note || '—'}</ReadOnlyValue>
              )}
            </Field>
          </div>
        </section>

        <DialogFooter className="items-center sm:justify-between">
          <p className="text-xs text-muted-foreground">
            {editable
              ? 'Sửa xong đóng lại rồi bấm Lưu của đơn mới có hiệu lực.'
              : 'Đơn đang khóa sửa chi phí.'}
          </p>
          <DialogClose asChild>
            <Button type="button" variant="outline">
              Đóng
            </Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

/** Câu "Nhập tay" trong popup: đã nhập bao nhiêu so với tiền khoản. */
function manualDialogStatus(cost: PurchaseOrderImportCost): string {
  const entered = manualAllocationTotal(cost)
  if (entered <= 0) return 'Gõ số tiền từng dòng ở bảng Chi phí theo dòng hàng'
  const target = costBaseAmount(cost)
  const gap = manualAllocationGap(cost)
  const tail =
    Math.abs(gap) <= MANUAL_ALLOCATION_TOLERANCE
      ? ' — đã khớp tổng'
      : ` — lệch ${formatMoney(Math.abs(gap))} đ`
  return `Đã nhập ${formatMoney(entered)} / ${formatMoney(target)} đ${tail}`
}
