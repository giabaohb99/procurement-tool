/** Nhà cung cấp — khớp `SupplierOut` của backend (`modules/supplier/schema.py`). */
export type Supplier = {
  id: number
  /** Tên viết tắt, duy nhất toàn hệ. */
  code: string
  /** Tên pháp lý đầy đủ. */
  name: string
  /** MÃ tiếng Anh (B-03): `company` | `individual` | `partnership` | `household`; rỗng = chưa chọn. */
  legal_type: string
  /** Nhãn tiếng Việt của `legal_type`, backend gửi kèm. Rỗng khi chưa chọn hoặc mã lạ. */
  legal_type_label: string
  tax_code: string
  address: string
  /** `goods` = NCC bán hàng, `transport` = đơn vị vận chuyển. */
  supplier_type: SupplierType
  contact_person: string
  phone: string
  payment_terms: string
  bank_account: string
  bank_name: string
  bank_account_name: string
  /** Thuế suất VAT dạng thập phân: 0.08 = 8%. */
  vat: number
  is_active: boolean
}

export type SupplierType = 'goods' | 'transport'

export const SUPPLIER_TYPE_LABELS: Record<SupplierType, string> = {
  goods: 'Nhà cung cấp hàng hóa',
  transport: 'Đơn vị vận chuyển',
}
