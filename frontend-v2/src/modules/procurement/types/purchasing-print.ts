/**
 * duoc-CR-777 — dữ liệu "Mẫu thu mua" của màn In YCMH từ ĐMH
 * (`GET /api/purchase-orders/{poId}/purchasing-print`).
 *
 * Khác mẫu thường ở bốn chỗ: người đề xuất = người ĐANG ĐĂNG NHẬP, trưởng phòng = QUẢN LÝ TRỰC TIẾP
 * của người đó, NCC = NCC của ĐƠN, bảng hàng = dòng của ĐƠN (bỏ dòng đã Hủy).
 */
export interface PurchasingPrintPerson {
  employee_id: number
  name: string
  position: string
  signature: string
}

export interface PurchasingPrintProposer extends PurchasingPrintPerson {
  department: string
}

export interface PurchasingPrintLine {
  line_id: number
  product_code: string
  product_name: string
  invoice_name: string
  spec: string
  item_group: string
  unit: string
  /** SL ĐẶT trên đơn. */
  qty: number
  price: number
  /** Phần trăm VAT (8 nghĩa là 8%). */
  vat: number
  /** Thành tiền GỒM VAT, theo nguyên tệ của đơn. */
  amount: number
}

export interface PurchasingPrintData {
  po_id: number
  po_code: string
  order_date: string
  currency: string
  proposer: PurchasingPrintProposer
  /** Hồ sơ chưa gán quản lý trực tiếp thì mọi trường rỗng. */
  manager: PurchasingPrintPerson
  /** Rỗng khi người xem thiếu `supplier.read`. */
  supplier: { code: string; name: string }
  supplier_hidden: boolean
  items: PurchasingPrintLine[]
  /** Tổng trước thuế. */
  subtotal: number
  vat: number
  /** Tổng gồm VAT. */
  total: number
}
