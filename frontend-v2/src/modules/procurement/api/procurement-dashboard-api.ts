import { apiGet } from '@/core/api'

/** Một cột của biểu đồ chi phí 12 tháng. */
export interface MonthlyCost {
  /** "T1".."T12". */
  label: string
  value: number
}

export interface NamedValue {
  name: string
  value: number
}

/** Việc cần xử lý — backend đã xếp sẵn theo mức độ. */
export interface DashboardAlert {
  type: string
  /** `danger` = quá hạn/trễ, `warn` = sắp tới hạn, còn lại là thông tin. */
  level: string
  title: string
  /** Đường dẫn của bản CŨ (`/purchase-orders/123`) — v2 phải tự đổi sang route mới. */
  link: string
}

export interface RecentPurchaseRequest {
  id: number
  code: string
  requester: string
  description: string
  department: string
  date: string
  status: string
  total: number
}

/**
 * `GET /api/dashboard/overview` — backend gom sẵn mọi số liệu của trang tổng
 * quan trong MỘT lần gọi (KPI, chi phí 12 tháng, cảnh báo, chứng từ gần đây) và
 * đã lọc theo phạm vi dữ liệu của người đang đăng nhập.
 */
export interface DashboardOverview {
  year: string
  kpi: {
    pr_pending: number
    sr_pending: number
    po_ordered: number
    late_deliveries: number
    survey_pending: number
    due_soon: number
    overdue: number
    contract_expiring: number
    inv_value: number
    out_of_stock: number
  }
  /** Giá trị NHẬN HÀNG theo tháng của năm đang xem. */
  cost_12m: MonthlyCost[]
  categories: { name: string; cost: number; pct: number }[]
  top_suppliers: NamedValue[]
  dept_spend: NamedValue[]
  po_status: { key: string; label: string; value: number }[]
  alerts: DashboardAlert[]
  alert_total: number
  recent_prs: RecentPurchaseRequest[]
}

export const procurementDashboardApi = {
  getOverview: () => apiGet<DashboardOverview>('/api/dashboard/overview'),
}
