import { apiGet } from '@/core/api'

import type { VehicleBooking } from '../types/vehicle-booking'

/** Một cột của biểu đồ (trạng thái / tháng). */
export interface LabeledValue {
  key?: number
  label: string
  value: number
}

/**
 * `GET /api/vehicle-bookings/overview` — Tổng quan Đặt xe theo VAI TRÒ.
 *
 * ⚠️ MỌI khối đều CÓ THỂ THIẾU: backend chỉ tính khối mà quyền/scope/hồ sơ tài xế
 * của người xem mở khóa (`mine` cần `create`, `approve` cần `approve`, `dispatch`
 * cần `write`+phạm vi ≥ phòng, `driver` cần hồ sơ tài xế, `company` cần phạm vi ≥
 * phòng). Khối bị gác thì khóa KHÔNG xuất hiện — giao diện chỉ vẽ khối nào có mặt.
 */
export interface BookingOverview {
  can: Record<string, boolean>
  /** Người dùng: phiếu của tôi, đếm theo trạng thái (khóa = mã trạng thái). */
  mine?: {
    by_status: Record<number, number>
    recent: VehicleBooking[]
  }
  /** Người duyệt / TBP: hàng chờ tôi duyệt. */
  approve?: {
    pending: number
    items: VehicleBooking[]
  }
  /** Điều phối viên: chờ điều phối + KPI đội xe. */
  dispatch?: {
    to_dispatch: number
    ongoing: number
    completed: number
    distance_sum: number
    cost_sum: number
    by_type: { car: number; delivery: number }
    queue: VehicleBooking[]
  }
  /** Tài xế: bảng chuyến được phân cho tôi. */
  driver?: {
    waiting: number
    accepted: number
    ongoing: number
    completed: number
    trips: VehicleBooking[]
  }
  /** Giám đốc / phạm vi ≥ phòng: tổng hợp toàn phạm vi (lọc theo khoảng ngày). */
  company?: {
    by_status: LabeledValue[]
    by_type: { car: number; delivery: number }
    by_company: { id: number; name: string; value: number }[]
    trend: LabeledValue[]
  }
  /** Điều phối viên / Giám đốc (quyền `approve`): thống kê theo xe & theo tài xế. */
  fleet?: {
    by_vehicle: { id: number; label: string; total: number; completed: number; distance_km: number; cost: number }[]
    by_driver: { id: number; name: string; total: number; completed: number; distance_km: number }[]
  }
}

/** Lọc khối tổng hợp theo khoảng ngày tạo (yyyy-mm-dd); bỏ trống = tất cả. */
export interface BookingOverviewParams {
  date_from?: string
  date_to?: string
}

export const vehicleBookingDashboardApi = {
  getOverview: (params?: BookingOverviewParams) =>
    apiGet<BookingOverview>('/api/vehicle-bookings/overview', { params }),
}
