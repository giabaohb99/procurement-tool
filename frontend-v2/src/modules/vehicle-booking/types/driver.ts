/** Tài xế trong danh mục Đặt xe (khớp DriverResponse của backend). */
export type Driver = {
  id: number
  name: string
  email: string
  phone: string
  license_number: string
  status: string
  is_external: boolean
  external_company: string
  /** Tài khoản đăng nhập liên kết (tài xế nội bộ); null/0 = chưa liên kết. */
  user_id: number | null
}

/** Nhãn trạng thái tài xế — hiển thị ở bảng/badge. */
export const DRIVER_STATUS_LABELS: Record<string, string> = {
  available: 'Sẵn sàng',
  on_leave: 'Nghỉ phép',
  on_trip: 'Đang chạy',
}
