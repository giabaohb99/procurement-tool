import {
  ALLOCATION_BY_VALUE,
  ALLOCATION_MANUAL,
  DEFAULT_CURRENCY,
  IMPORT_COST_TAX_TYPES,
  IMPORT_COST_TYPE_OPTIONS,
  MANUAL_ALLOCATION_TOLERANCE,
  ORDER_TYPE_DOMESTIC,
  ORDER_TYPE_IMPORT,
  STATE_BUDGET_SUPPLIER_CODE,
  STATE_BUDGET_SUPPLIER_NAME,
  importCostTypeLabel,
  type ImportCostAllocation,
  type PoCostType,
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

/**
 * bao-CR-364 (port v2) — nhãn tiền tệ của một bảng TỔNG phải lấy từ các DÒNG, không lấy
 * từ đầu phiếu. Từ bao-CR-319 mỗi dòng mang tiền tệ + tỷ giá riêng, đầu phiếu chỉ là mặc
 * định cho dòng để trống. Đầu phiếu `VND` mà dòng `USD` là chuyện bình thường (PO00122 prod:
 * 6.500 USD × 26.500 = 172.250.000 đ) — dán nhãn theo đầu phiếu ra ngay "6.500 VND".
 *
 * `mixed = true` khi các dòng KHÔNG cùng một loại tiền: cộng ngang các dòng là vô nghĩa
 * (USD cộng VND), nơi gọi phải chuyển sang bày bản quy đổi VNĐ thay vì dán đại một nhãn.
 * Dòng để trống tiền tệ thì theo `fallback` (tiền tệ đầu phiếu).
 */
export function resolveTotalsCurrency(
  lineCurrencies: (string | null | undefined)[],
  fallback: string,
): { currency: string; mixed: boolean } {
  const base = (fallback || DEFAULT_CURRENCY).trim().toUpperCase() || DEFAULT_CURRENCY
  const found: string[] = []
  for (const raw of lineCurrencies) {
    const code = String(raw ?? '').trim().toUpperCase() || base
    if (!found.includes(code)) found.push(code)
  }
  return { currency: found.length === 1 ? found[0] : base, mixed: found.length > 1 }
}

/** Ba dòng tổng cuối bảng dòng hàng ĐMH + tiền tệ để dán nhãn (bao-CR-364). */
export interface OrderTotals {
  subtotal: number
  vat: number
  total: number
  /** Tiền tệ của ba con số trên. Đơn trộn nhiều loại tiền thì luôn là VND (đã quy đổi). */
  currency: string
  /** Các dòng KHÔNG cùng một loại tiền — ba dòng tổng đang là bản quy đổi VNĐ. */
  mixed: boolean
}

/**
 * Tổng tiền theo SL ĐẶT của đơn, tính tại chỗ để thấy ngay khi gõ. Dòng cùng một loại tiền
 * thì cộng thẳng nguyên tệ; trộn nhiều loại tiền thì mỗi dòng nhân tỷ giá của chính nó rồi
 * mới cộng (bản quy đổi VNĐ), vì cộng ngang USD với VND ra một con số vô nghĩa.
 */
export function summarizeOrderTotals(
  order: Pick<PurchaseOrderDetail, 'currency' | 'exchange_rate' | 'items'>,
): OrderTotals {
  const items = order.items ?? []
  const { currency, mixed } = resolveTotalsCurrency(
    items.map((item) => item.currency),
    order.currency,
  )
  let subtotal = 0
  let total = 0
  for (const item of items) {
    const gross = (Number(item.qty_order) || 0) * (Number(item.price) || 0)
    const withVat = gross * (1 + (Number(item.vat) || 0) / 100)
    if (mixed) {
      const { exchangeRate } = resolveLineCurrency(item, order)
      subtotal += gross * exchangeRate
      total += displayLineBaseAmount(item, order)
    } else {
      subtotal += gross
      total += withVat
    }
  }
  return {
    subtotal,
    vat: total - subtotal,
    total,
    currency: mixed ? DEFAULT_CURRENCY : currency,
    mixed,
  }
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

/**
 * Tiền KHOẢN chi phí theo giai đoạn chỉ định: gồm VAT, quy đổi VNĐ.
 *
 * Dùng để tính nhanh trên màn trước khi Lưu; sau khi lưu server trả về `base_amount`
 * / `effective_base` chính xác hơn qua `displayCostBaseAmount`.
 *
 * `stage` mặc định 1 (Dự toán) nếu không rõ. Thường truyền `order.cost_stage`.
 */
export function costBaseAmount(
  cost: Pick<
    PurchaseOrderImportCost,
    | 'estimate_amount'
    | 'estimate_rate'
    | 'provisional_amount'
    | 'provisional_rate'
    | 'final_amount'
    | 'final_rate'
    | 'line_stage'
    | 'vat'
    | 'currency'
  >,
  orderStage = 1,
): number {
  const effectiveStage = Math.max(orderStage, Number(cost.line_stage) || 1)
  let amount: number | null | undefined
  let rate: number
  if (effectiveStage >= 3) {
    amount = cost.final_amount
    rate = cost.final_rate ?? 1
  } else if (effectiveStage >= 2) {
    amount = cost.provisional_amount
    rate = cost.provisional_rate ?? 1
  } else {
    amount = cost.estimate_amount
    rate = cost.estimate_rate ?? 1
  }
  return (Number(amount) || 0) * (1 + (Number(cost.vat) || 0) / 100) * effectiveExchangeRate(cost.currency, rate)
}

export function sumCostBase(costs: PurchaseOrderImportCost[], orderStage = 1): number {
  return costs.reduce((sum, cost) => sum + costBaseAmount(cost, orderStage), 0)
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

export function displayCostBaseAmount(cost: PurchaseOrderImportCost, orderStage = 1): number {
  // `base_amount` / `effective_base` là alias backend tính; ưu tiên dùng khi có.
  const stored = Number(cost.base_amount ?? cost.effective_base)
  return stored > 0 ? stored : costBaseAmount(cost, orderStage)
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
export function groupCostsByType(costs: PurchaseOrderImportCost[], orderStage = 1): CostTypeGroup[] {
  const groups = new Map<number, CostTypeGroup>()
  for (const cost of costs) {
    const key = Number(cost.cost_type) || 99
    const current = groups.get(key) ?? {
      cost_type: key,
      label: cost.cost_type_label || cost.cost_type_name || importCostTypeLabel(key),
      base_amount: 0,
      count: 0,
    }
    current.base_amount += displayCostBaseAmount(cost, orderStage)
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

export function groupCostsBySupplier(costs: PurchaseOrderImportCost[], orderStage = 1): CostSupplierGroup[] {
  const groups = new Map<string, CostSupplierGroup>()
  for (const cost of costs) {
    const key = cost.supplier_code || ''
    const current = groups.get(key) ?? {
      supplier_code: key,
      supplier_name: cost.supplier_name || key,
      base_amount: 0,
      count: 0,
    }
    current.base_amount += displayCostBaseAmount(cost, orderStage)
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
  // Sau bao-CR-453: số tiền hiệu lực nằm trong `base_amount` / `effective_base`.
  // Dòng chưa quyết toán thì không sinh công nợ.
  const effectiveBase = Number(cost.base_amount ?? cost.effective_base)
  if (!cost.supplier_code || !(effectiveBase > 0)) {
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
 * Danh sách loại chi phí cho ô chọn trên thẻ chi phí.
 *
 * Ưu tiên danh mục lấy từ `/api/po-cost-types`; danh mục chưa nạp (hoặc người
 * dùng thiếu quyền đọc) thì rơi về bộ mã cứng cũ. Loại đang gắn trên dòng mà đã
 * bị tắt trong danh mục vẫn phải còn trong danh sách, kèm chữ «(đã tắt)» — nếu
 * không thì mở đơn cũ ra là ô chọn nhảy sang loại khác.
 */
export function buildCostTypeOptions(
  catalog: PoCostType[],
  currentCode: number,
  currentLabel = '',
): { value: number; label: string }[] {
  if (catalog.length === 0) return IMPORT_COST_TYPE_OPTIONS.map((o) => ({ ...o }))
  const sorted = [...catalog].sort(
    (a, b) => a.sort_order - b.sort_order || a.code - b.code,
  )
  const options = sorted.map((type) => ({ value: Number(type.code), label: type.name }))
  if (currentCode && !options.some((o) => o.value === Number(currentCode))) {
    const name = currentLabel || importCostTypeLabel(currentCode)
    options.push({ value: Number(currentCode), label: `${name} (đã tắt)` })
  }
  return options
}

/** Tìm một dòng danh mục theo mã loại chi phí. */
export function findCostType(catalog: PoCostType[], code: number): PoCostType | undefined {
  return catalog.find((type) => Number(type.code) === Number(code))
}

/**
 * Đổi loại chi phí.
 * - Thuế / phí nộp nhà nước tự điền NCC "Ngân sách nhà nước" khi ô NCC còn trống.
 * - Đổi ngược từ thuế sang loại thường thì xóa NSNN đi kẻo cước tàu ghi nợ nhà nước.
 * - Nếu có `costTypeRecord` từ danh mục: tự điền NCC/phân bổ/VAT mặc định khi ô đang trống
 *   (E06 — không ghi đè ô đã gõ).
 */
export function applyCostType(
  cost: PurchaseOrderImportCost,
  costType: number,
  costTypeRecord?: PoCostType,
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

  // E06 — tự điền từ danh mục khi ô đang trống
  if (costTypeRecord) {
    if (!next.supplier_code && costTypeRecord.default_supplier_code) {
      next.supplier_code = costTypeRecord.default_supplier_code
    }
    if (
      (!next.allocation_method || next.allocation_method === ALLOCATION_BY_VALUE) &&
      costTypeRecord.default_allocation_method
    ) {
      next.allocation_method = costTypeRecord.default_allocation_method
    }
    if (!next.vat && costTypeRecord.default_vat) {
      next.vat = costTypeRecord.default_vat
    }
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
export function manualAllocationGap(cost: PurchaseOrderImportCost, orderStage = 1): number {
  const gap = displayCostBaseAmount(cost, orderStage) - manualAllocationTotal(cost)
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

/**
 * bao-CR-453 — lấy dữ liệu phân bổ cho một giai đoạn từ dict nhiều giai đoạn.
 *
 * Mặc định dùng giai đoạn hiện hành của đơn (`String(costStage)`); "effective" là
 * giai đoạn hiệu lực dùng cho bản in.
 */
export function getAllocationForStage(
  allocationByStage: Record<string, ImportCostAllocation> | null | undefined,
  stageKey: string | number,
): ImportCostAllocation | undefined {
  if (!allocationByStage) return undefined
  const key = String(stageKey)
  return allocationByStage[key]
}

/**
 * bao-CR-453 — các khóa giai đoạn có số liệu (có ít nhất một dòng chia).
 * Dùng để tắt nút giai đoạn trên khối "Chi phí theo dòng hàng" khi không có số.
 */
export function availableAllocationStages(
  allocationByStage: Record<string, ImportCostAllocation> | null | undefined,
): Set<string> {
  if (!allocationByStage) return new Set()
  return new Set(
    Object.entries(allocationByStage)
      .filter(([, data]) => (data?.lines?.length ?? 0) > 0)
      .map(([key]) => key),
  )
}
