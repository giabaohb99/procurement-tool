/** Xe trong danh mục Đặt xe (khớp VehicleResponse của backend). */
export type Vehicle = {
  id: number
  license_plate: string
  model: string
  type: string
  capacity: number
  status: string
  is_external: boolean
  external_company: string
}

/** Nhãn trạng thái xe — hiển thị ở bảng/badge. */
export const VEHICLE_STATUS_LABELS: Record<string, string> = {
  available: 'Sẵn sàng',
  maintenance: 'Bảo trì',
  on_trip: 'Đang chạy',
}
