import {
  ALLOCATION_BY_VALUE,
  ALLOCATION_MANUAL,
  DEFAULT_CURRENCY,
  IMPORT_COST_TAX_TYPES,
  MANUAL_ALLOCATION_TOLERANCE,
  ORDER_TYPE_DOMESTIC,
  ORDER_TYPE_IMPORT,
  STATE_BUDGET_SUPPLIER_CODE,
  STATE_BUDGET_SUPPLIER_NAME,
  importCostTypeLabel,
  type PurchaseOrderDetail,
  type PurchaseOrderImportCost,
  type PurchaseOrderItem,
} from '../types/purchase-order-detail'

/**
 * bao-CR-319 — phép tính thuần của đơn NHẬP KHẨU: quy đổi VNĐ, chi phí lô hàng và
 * chia nhập tay. Backend là nguồn sự thật (`base_amount`, `import_cost_summary`,
 * `import_cost_allocation`); các hàm ở đây chỉ để màn hình nhìn thấy số NGAY lúc gõ,
 * trước khi Lưu — nên công thức phải khớp `service.py`.
 */

/** Tỷ giá hiệu lực: VND luôn là 1; ngoại tệ chưa nhập tỷ giá thì 0 (chưa quy đổi được). */
export function effectiveExchangeRate(currency: string, exchangeRate: number): number {
  const code = (currency || DEFAULT_CURRENCY).toUpperCase()
  if (code === DEFAULT_CURRENCY) return 1
  const rate = Number(exchangeRate)
  return Number.isFinite(rate) && rate > 0 ? rate : 0
}

/** Đồng tiền / tỷ giá của DÒNG: để trống thì theo đơn. */
export function resolveLineCurrency(
  item: Pick<PurchaseOrderItem, 'currency' | 'exchange_rate'>,
  order: Pick<PurchaseOrderDetail, 'currency' | 'exchange_rate'>,
): { currency: string; exchangeRate: number } {
  const currency = (item.currency || order.currency || DEFAULT_CURRENCY).toUpperCase()
  const ownRate = Number(item.exchange_rate)
  const exchangeRate = ownRate > 0 ? ownRate : Number(order.exchange_rate) || 0
  return { currency, exchangeRate: effectiveExchangeRate(currency, exchangeRate) }
}

/** Thành tiền quy đổi VNĐ của dòng theo SL ĐẶT (gồm VAT dòng). */
export function lineBaseAmount(
  item: Pick<PurchaseOrderItem, 'qty_order' | 'price' | 'vat' | 'currency' | 'exchange_rate'>,
  order: Pick<PurchaseOrderDetail, 'currency' | 'exchange_rate'>,
): number {
  const { exchangeRate } = resolveLineCurrency(item, order)
  const gross = (Number(item.qty_order) || 0) * (Number(item.price) || 0)
  return gross * (1 + (Number(item.vat) || 0) / 100) * exchangeRate
}

/** Tiền KHOẢN chi phí: gồm VAT, quy đổi VNĐ theo tỷ giá của chính khoản. */
export function costBaseAmount(
  cost: Pick<PurchaseOrderImportCost, 'amount' | 'vat' | 'currency' | 'exchange_rate'>,
): number {
  const rate = effectiveExchangeRate(cost.currency, cost.exchange_rate)
  return (Number(cost.amount) || 0) * (1 + (Number(cost.vat) || 0) / 100) * rate
}

export function sumCostBase(costs: PurchaseOrderImportCost[]): number {
  return costs.reduce((sum, cost) => sum + costBaseAmount(cost), 0)
}

/**
 * Số quy đổi để BÀY: backend đã tính `base_amount` thì lấy, chưa có (dòng mới) hoặc
 * bằng 0 thì tính tại chỗ. Dùng `??` là dính bẫy `0 ?? x = 0` — đơn nháp USD chưa
 * lưu hiện "0 đ" cả cột (khách báo 09/09/2026).
 */
export function displayLineBaseAmount(
  item: Pick<
    PurchaseOrderItem,
    'qty_order' | 'price' | 'vat' | 'currency' | 'exchange_rate' | 'base_amount'
  >,
  order: Pick<PurchaseOrderDetail, 'currency' | 'exchange_rate'>,
): number {
  const stored = Number(item.base_amount)
  return stored > 0 ? stored : lineBaseAmount(item, order)
}

export function displayCostBaseAmount(cost: PurchaseOrderImportCost): number {
  const stored = Number(cost.base_amount)
  return stored > 0 ? stored : costBaseAmount(cost)
}

/** Dòng ngoại tệ mà cả dòng lẫn đơn đều chưa có tỷ giá — màn hình phải nói rõ thay vì "0 đ". */
export function isMissingExchangeRate(
  item: Pick<PurchaseOrderItem, 'currency' | 'exchange_rate'>,
  order: Pick<PurchaseOrderDetail, 'currency' | 'exchange_rate'>,
): boolean {
  const { currency, exchangeRate } = resolveLineCurrency(item, order)
  return currency !== DEFAULT_CURRENCY && exchangeRate <= 0
}

/** Một dòng của bảng "Theo loại chi phí" — gom từ các khoản đang có trên màn. */
export interface CostTypeGroup {
  cost_type: number
  label: string
  base_amount: number
  count: number
}

/** Gom khoản theo loại, xếp tiền giảm dần — tính ngay trên nháp, không chờ Lưu. */
export function groupCostsByType(costs: PurchaseOrderImportCost[]): CostTypeGroup[] {
  const groups = new Map<number, CostTypeGroup>()
  for (const cost of costs) {
    const key = Number(cost.cost_type) || 99
    const current = groups.get(key) ?? {
      cost_type: key,
      label: cost.cost_type_label || importCostTypeLabel(key),
      base_amount: 0,
      count: 0,
    }
    current.base_amount += displayCostBaseAmount(cost)
    current.count += 1
    groups.set(key, current)
  }
  return Array.from(groups.values()).sort((a, b) => b.base_amount - a.base_amount)
}

/** Một dòng của bảng "Theo nhà cung cấp" khi đơn chưa có công nợ (chưa duyệt / chưa lưu). */
export interface CostSupplierGroup {
  supplier_code: string
  supplier_name: string
  base_amount: number
  count: number
}

export function groupCostsBySupplier(costs: PurchaseOrderImportCost[]): CostSupplierGroup[] {
  const groups = new Map<string, CostSupplierGroup>()
  for (const cost of costs) {
    const key = cost.supplier_code || ''
    const current = groups.get(key) ?? {
      supplier_code: key,
      supplier_name: cost.supplier_name || key,
      base_amount: 0,
      count: 0,
    }
    current.base_amount += displayCostBaseAmount(cost)
    current.count += 1
    groups.set(key, current)
  }
  return Array.from(groups.values()).sort((a, b) => b.base_amount - a.base_amount)
}

/** Tỷ lệ phần trăm để bày, tránh chia cho 0. */
export function percentOf(part: number, whole: number): number {
  if (!(whole > 0)) return 0
  return (part / whole) * 100
}

/**
 * Lý do một khoản CHƯA tick tạo YCTT được. Trả `null` khi tick được.
 * Khớp chữ v1 để người dùng quen bản cũ không phải học lại.
 */
export function paymentBlockReason(
  cost: PurchaseOrderImportCost,
  orderApproved: boolean,
): string | null {
  if (!cost.id) return 'Chưa thành công nợ (dòng mới chưa Lưu)'
  if (!cost.supplier_code || !(Number(cost.amount) > 0)) {
    return 'Chưa thành công nợ (chưa chọn NCC hoặc số tiền 0)'
  }
  if (!orderApproved) return 'Chưa thành công nợ (đơn chưa duyệt)'
  if (!cost.payable_id) return 'Chưa thành công nợ'
  if ((cost.remaining ?? 0) <= 0.01) return 'Đã chi đủ'
  return null
}

/**
 * Đổi cách chia của một khoản. Chuyển sang NHẬP TAY thì điền sẵn số backend đang
 * chia (nếu có) để người dùng chỉ sửa chỗ lệch, khỏi gõ lại từ đầu (giống v1).
 */
export function switchAllocationMethod(
  cost: PurchaseOrderImportCost,
  method: number,
  allocationLines: { item_id: number; costs: { cost_id: number; base_amount: number }[] }[],
): PurchaseOrderImportCost {
  const next = { ...cost, allocation_method: Number(method) }
  if (Number(method) !== ALLOCATION_MANUAL) return next
  if (Object.keys(cost.manual_allocation ?? {}).length > 0) return next
  const manual: Record<string, number> = {}
  for (const line of allocationLines) {
    const share = line.costs.find((entry) => entry.cost_id === cost.id)
    if (share && share.base_amount > 0) manual[String(line.item_id)] = Math.round(share.base_amount)
  }
  return { ...next, manual_allocation: manual }
}

export function isTaxCostType(costType: number): boolean {
  return IMPORT_COST_TAX_TYPES.includes(Number(costType))
}

/**
 * Đổi loại chi phí. Thuế / phí nộp nhà nước tự điền NCC "Ngân sách nhà nước" khi ô NCC
 * còn trống; đổi ngược từ thuế sang loại thường thì xóa NSNN đi kẻo cước tàu lại ghi
 * nợ cho nhà nước.
 */
export function applyCostType(
  cost: PurchaseOrderImportCost,
  costType: number,
): PurchaseOrderImportCost {
  const next = { ...cost, cost_type: Number(costType) }
  const isStateBudget = cost.supplier_code === STATE_BUDGET_SUPPLIER_CODE
  if (isTaxCostType(next.cost_type)) {
    if (!cost.supplier_code || isStateBudget) {
      next.supplier_code = STATE_BUDGET_SUPPLIER_CODE
      next.supplier_name = STATE_BUDGET_SUPPLIER_NAME
    }
  } else if (isStateBudget) {
    next.supplier_code = ''
    next.supplier_name = ''
  }
  return next
}

export function isManualAllocation(cost: Pick<PurchaseOrderImportCost, 'allocation_method'>) {
  return Number(cost.allocation_method) === ALLOCATION_MANUAL
}

/** Tổng các dòng đã nhập tay của một khoản. */
export function manualAllocationTotal(
  cost: Pick<PurchaseOrderImportCost, 'manual_allocation'>,
): number {
  return Object.values(cost.manual_allocation ?? {}).reduce(
    (sum, value) => sum + (Number(value) || 0),
    0,
  )
}

/** Lệch giữa tiền khoản (quy đổi) và tổng nhập tay; 0 = khớp trong dung sai. */
export function manualAllocationGap(cost: PurchaseOrderImportCost): number {
  const gap = costBaseAmount(cost) - manualAllocationTotal(cost)
  return Math.abs(gap) <= MANUAL_ALLOCATION_TOLERANCE ? 0 : gap
}

/** Ghi số nhập tay cho một dòng hàng; 0 / NaN thì bỏ khóa cho gọn. */
export function setManualAllocation(
  cost: PurchaseOrderImportCost,
  itemId: number,
  value: number,
): PurchaseOrderImportCost {
  const manual = { ...(cost.manual_allocation ?? {}) }
  const key = String(itemId)
  const amount = Number(value)
  if (Number.isFinite(amount) && amount !== 0) manual[key] = amount
  else delete manual[key]
  return { ...cost, manual_allocation: manual }
}

/**
 * Đổi loại đơn. Về TRONG NƯỚC thì trả đơn về VND / tỷ giá 1 và bỏ chi phí lô hàng
 * (backend cũng bỏ). Sang NHẬP KHẨU thì VAT dòng về 0: thuế GTGT hàng nhập là một
 * KHOẢN chi phí lô hàng nộp cho hải quan, không nằm trong giá NCC nước ngoài.
 */
export function switchOrderType(
  data: PurchaseOrderDetail,
  orderType: number,
): Partial<PurchaseOrderDetail> {
  if (Number(orderType) === ORDER_TYPE_IMPORT) {
    return {
      order_type: ORDER_TYPE_IMPORT,
      items: data.items.map((item) => ({ ...item, vat: 0 })),
    }
  }
  return {
    order_type: ORDER_TYPE_DOMESTIC,
    currency: DEFAULT_CURRENCY,
    exchange_rate: 1,
    customs_decl_no: '',
    customs_decl_date: '',
    import_costs: [],
    items: data.items.map((item) => ({
      ...item,
      currency: '',
      exchange_rate: 0,
    })),
  }
}

/** Cách chia mặc định khi thêm khoản mới. */
export const DEFAULT_ALLOCATION_METHOD = ALLOCATION_BY_VALUE
