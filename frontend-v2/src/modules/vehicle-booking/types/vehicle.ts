/** Xe trong danh mục Đặt xe (khớp VehicleResponse của backend). */
export type Vehicle = {
  id: number
  license_plate: string
  model: string
  type: string
  capacity: number
  status: string
  is_external: boolean
  /** Tên đơn vị / doanh nghiệp cho thuê (xe thuê ngoài). */
  external_company: string
  /** Xe thuê ngoài là doanh nghiệp hay cá nhân (dùng SUPPLIER_TYPE ở types/driver). */
  supplier_type: number
  supplier_type_label: string
  /** MST (doanh nghiệp). */
  tax_code: string
  /** Địa chỉ thuế (doanh nghiệp). */
  tax_address: string
  /** CCCD (cá nhân). */
  id_number: string
}

/** Nhãn trạng thái xe — hiển thị ở bảng/badge. */
export const VEHICLE_STATUS_LABELS: Record<string, string> = {
  available: 'Sẵn sàng',
  maintenance: 'Bảo trì',
  on_trip: 'Đang chạy',
  inactive: 'Ngưng sử dụng',
}
