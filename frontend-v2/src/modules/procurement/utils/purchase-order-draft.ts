import type { PurchaseOrderPayload } from '../api/purchase-order-api'
import type {
  PurchaseRequestDetail,
  PurchaseRequestItem,
} from '../types/purchase-request-detail'
import type { PurchaseOrderDetail, PurchaseOrderItem } from '../types/purchase-order-detail'

/**
 * Dữ liệu điền sẵn khi tạo ĐMH TỪ một phiếu YCMH. Đi kèm điều hướng
 * (`navigate(..., { state })`) — CHƯA ghi gì vào DB cho tới khi bấm Tạo đơn.
 */
export interface PurchaseOrderDraftFromRequest {
  pr_code: string
  company_id: number
  department: string
  nspt: string
  supplier_code: string
  supplier_name: string
  vat_rate: number
  is_urgent: boolean
  note: string
  items: PurchaseOrderItem[]
}

/** Đơn trống cho màn tạo mới; có `from` thì điền sẵn theo phiếu YCMH nguồn. */
export function createEmptyPurchaseOrder(
  from?: PurchaseOrderDraftFromRequest,
): PurchaseOrderDetail {
  return {
    id: 0,
    code: '',
    misa_code: '',
    pr_code: from?.pr_code ?? '',
    survey_code: '',
    company_id: from?.company_id ?? 0,
    supplier_code: from?.supplier_code ?? '',
    supplier_name: from?.supplier_name ?? '',
    department: from?.department ?? '',
    nspt: from?.nspt ?? '',
    order_date: new Date().toISOString().slice(0, 10),
    vat_rate: from?.vat_rate ?? 0.08,
    payment_terms: '',
    is_urgent: from?.is_urgent ?? false,
    status: 'draft',
    document_status: '',
    note: from?.note ?? '',
    items: from?.items ?? [],
    subtotal: 0,
    vat: 0,
    total: 0,
    shipping_total: 0,
    order_subtotal: 0,
    order_total: 0,
    unpaid_total: 0,
  }
}

/** Lọc bỏ các cột do backend tính; chỉ gửi đúng phần người dùng nhập. */
export function toPurchaseOrderPayload(data: PurchaseOrderDetail): PurchaseOrderPayload {
  return {
    misa_code: data.misa_code,
    pr_code: data.pr_code,
    survey_code: data.survey_code,
    company_id: Number(data.company_id) || 0,
    supplier_code: data.supplier_code,
    supplier_name: data.supplier_name,
    department: data.department,
    nspt: data.nspt,
    order_date: data.order_date,
    vat_rate: Number(data.vat_rate) || 0,
    payment_terms: data.payment_terms,
    is_urgent: data.is_urgent,
    note: data.note,
    items: data.items
      .filter((item) => item.product_name.trim() || item.product_code.trim())
      .map((item) => ({
        id: item.id,
        product_code: item.product_code,
        product_name: item.product_name,
        invoice_name: item.invoice_name,
        item_group: item.item_group,
        spec: item.spec,
        fg_code: item.fg_code,
        fg_name: item.fg_name,
        invoice_no: item.invoice_no,
        invoice_date: item.invoice_date,
        document_delivery_date: item.document_delivery_date,
        supplier_ready: !!item.supplier_ready,
        required_date: item.required_date,
        expected_date: item.expected_date,
        unit: item.unit,
        qty_request: Number(item.qty_request) || 0,
        qty_order: Number(item.qty_order) || 0,
        price: Number(item.price) || 0,
        vat: Number(item.vat) || 0,
        warehouse_code: item.warehouse_code,
        note: item.note,
        deliveries: item.deliveries ?? [],
      })),
  }
}

/** Kết quả dựng dòng ĐMH từ phiếu YCMH. */
export interface PurchaseOrderLinesFromRequest {
  /** Dòng còn thiếu hàng — số lượng = yêu cầu trừ đã đặt. */
  remaining: PurchaseOrderItem[]
  /** Dòng đã đặt đủ/vượt — chỉ đưa vào khi người dùng chọn mua thêm. */
  exceeded: PurchaseOrderItem[]
  /** Mô tả dòng đã đặt đủ/vượt để cảnh báo. */
  exceededMessages: string[]
}

/**
 * Dựng dòng ĐMH từ phiếu YCMH đã điều phối.
 *
 * Số lượng mặc định là phần CÒN THIẾU (yêu cầu − đã đặt ở các ĐMH trước) chứ
 * không phải toàn bộ số yêu cầu: một phiếu thường tách thành nhiều đơn theo NCC.
 * Dòng "Hủy đơn" bị loại hẳn.
 */
export function buildPurchaseOrderLines(
  items: PurchaseRequestItem[],
  orderedByCode: Record<string, number> = {},
): PurchaseOrderLinesFromRequest {
  const remaining: PurchaseOrderItem[] = []
  const exceeded: PurchaseOrderItem[] = []
  const exceededMessages: string[] = []

  for (const item of items) {
    if (!item.product_name || item.line_status === 'cancelled') continue

    const requested = Number(item.qty) || 0
    const ordered = Number(orderedByCode[item.product_code] || 0)
    const left = requested - ordered

    if (left > 0) {
      remaining.push(toOrderLine(item, left))
    } else {
      exceeded.push(toOrderLine(item, requested))
      exceededMessages.push(`${item.product_name} (đã đặt ${ordered}/${requested})`)
    }
  }

  return { remaining, exceeded, exceededMessages }
}

function toOrderLine(item: PurchaseRequestItem, qty: number): PurchaseOrderItem {
  return {
    product_code: item.product_code,
    product_name: item.product_name,
    invoice_name: '',
    item_group: item.item_group,
    spec: '',
    fg_code: '',
    fg_name: '',
    invoice_no: '',
    invoice_date: '',
    document_delivery_date: '',
    supplier_ready: true,
    // Ngày cần hàng ở YCMH → Ngày yêu cầu có hàng ở ĐMH.
    required_date: item.required_date || '',
    // TG dự kiến có hàng ở YCMH → Ngày dự kiến có hàng ở ĐMH. Rỗng thì backend
    // tự tính theo thời gian chuẩn của phân loại.
    expected_date: item.expected_date || '',
    unit: item.unit,
    qty_request: qty,
    qty_order: qty,
    price: Number(item.price) || 0,
    // VAT theo TỪNG DÒNG của YCMH, không lấy mức chung của đơn.
    vat: Number(item.vat_pct) || 0,
    warehouse_code: '',
    note: item.note || '',
    deliveries: [],
  }
}

/** Gói dữ liệu điền sẵn để điều hướng sang màn tạo ĐMH. */
export function toDraftFromRequest(
  request: PurchaseRequestDetail,
  items: PurchaseOrderItem[],
): PurchaseOrderDraftFromRequest {
  return {
    pr_code: request.code,
    company_id: request.company_id,
    department: request.department,
    // NSPT = người phụ trách dòng ở YCMH; để trống thì backend tự lấy người tạo.
    nspt: request.items.find((item) => item.assignee)?.assignee ?? '',
    supplier_code: '',
    supplier_name: request.supplier_pur?.name || request.suggested_supplier || '',
    vat_rate: Number(request.vat_rate) || 0.08,
    is_urgent: !!request.is_urgent,
    note: request.note || '',
    items,
  }
}
