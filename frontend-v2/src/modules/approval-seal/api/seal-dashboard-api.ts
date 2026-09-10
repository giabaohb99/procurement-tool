import { apiGet } from '@/core/api'

import type { SealRequest } from '../types/seal-request'

export interface LabeledValue {
  key?: number
  label: string
  value: number
}

/**
 * `GET /api/seal-requests/overview` — Tổng quan Duyệt dấu theo VAI TRÒ.
 *
 * Khối theo vai trò (đặt ở CỘT 2 của hàng bảng): `approve` (TBP — Chờ phê duyệt),
 * `clerk` (Văn thư — Chờ đóng dấu), `director` (Giám đốc — Yêu cầu đã phê duyệt).
 * `mine` = Phiếu gần đây của tôi (cột 1). `stats` = thống kê theo phạm vi RIÊNG
 * của người xem (mọi vai trò). Khối bị gác thì khóa KHÔNG xuất hiện.
 */
export interface SealOverview {
  can: Record<string, boolean>
  mine?: {
    by_status: Record<number, number>
    recent: SealRequest[]
  }
  approve?: {
    pending: number
    items: SealRequest[]
  }
  clerk?: {
    to_stamp: number
    completed: number
    queue: SealRequest[]
  }
  /** Giám đốc (chỉ đọc, phạm vi công ty) — yêu cầu đã phê duyệt của công ty mình. */
  director?: {
    count: number
    items: SealRequest[]
  }
  /** Thống kê theo tháng / trạng thái / công ty — của MỌI vai trò, theo phạm vi riêng. */
  stats?: {
    by_status: LabeledValue[]
    by_company: { id: number; name: string; value: number }[]
    trend: LabeledValue[]
  }
}

/** Lọc MỌI khối báo cáo theo khoảng ngày tạo (yyyy-mm-dd); bỏ trống = tất cả. */
export interface SealOverviewParams {
  date_from?: string
  date_to?: string
}

export const sealDashboardApi = {
  getOverview: (params?: SealOverviewParams) =>
    apiGet<SealOverview>('/api/seal-requests/overview', { params }),
}
