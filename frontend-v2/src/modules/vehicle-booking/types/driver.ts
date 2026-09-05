/** Tài xế trong danh mục Đặt xe (khớp DriverResponse của backend). */
export type Driver = {
  id: number
  name: string
  email: string
  phone: string
  /** Số giấy phép lái xe. */
  license_number: string
  /** Hạng GPLX (B2/C/D…) — tách riêng khỏi số GPLX. */
  license_class: string
  status: string
  is_external: boolean
  /** Tên đơn vị / doanh nghiệp cung cấp (tài xế thuê ngoài). */
  external_company: string
  /** Tài xế thuê ngoài là doanh nghiệp hay cá nhân (xem SUPPLIER_TYPE). */
  supplier_type: number
  supplier_type_label: string
  /** MST (doanh nghiệp). */
  tax_code: string
  /** Địa chỉ thuế (doanh nghiệp). */
  tax_address: string
  /** CCCD (cá nhân). */
  id_number: string
  /** Tài khoản đăng nhập liên kết (tài xế nội bộ); null/0 = chưa liên kết. */
  user_id: number | null
}

/** Nguồn tài xế thuê ngoài — khớp hằng số SUPPLIER_* của backend. */
export const SUPPLIER_TYPE = {
  none: 0,
  enterprise: 1, // doanh nghiệp: tên DN + MST + địa chỉ thuế
  individual: 2, // cá nhân: CCCD
} as const

/** Nhãn trạng thái tài xế — hiển thị ở bảng/badge. */
export const DRIVER_STATUS_LABELS: Record<string, string> = {
  available: 'Sẵn sàng',
  on_leave: 'Nghỉ phép',
  on_trip: 'Đang chạy',
  inactive: 'Ngưng sử dụng',
}
