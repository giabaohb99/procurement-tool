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

export interface LowStockItem {
  product_code: string
  product_name: string
  qty: number
  unit: string
  warehouse_code: string
}

/** Một kho trong `kpi_inv_by_warehouse`. `warehouse_code = ""` = dòng tồn chưa gán kho. */
export interface InventoryByWarehouse {
  warehouse_code: string
  /** Kho chưa có trong danh mục thì máy chủ trả bằng mã kho. */
  warehouse_name: string
  /** Tổng giá trị tồn của kho, VND. */
  value: number
  /** Số dòng tồn (mã hàng) của kho. */
  lines: number
}

/**
 * `GET /api/dashboard/overview` — backend gom sẵn mọi số liệu của trang tổng
 * quan trong MỘT lần gọi (KPI, chi phí 12 tháng, cảnh báo, chứng từ gần đây) và
 * đã lọc theo phạm vi dữ liệu của người đang đăng nhập.
 */
export interface DashboardOverview {
  year: string
  /**
   * Mọi khóa đều CÓ THỂ THIẾU: backend chỉ tính khối nào người dùng có quyền
   * Xem entity tương ứng (`pr_pending` cần `purchase_request`, `due_soon` /
   * `overdue` cần `payable`…), khối bị gác thì khóa không xuất hiện. Luôn đọc
   * kèm `?? 0` và đừng mượn khóa của phân hệ khác để lấp chỗ trống.
   */
  kpi: {
    pr_pending?: number
    sr_pending?: number
    po_ordered?: number
    late_deliveries?: number
    survey_pending?: number
    due_soon?: number
    overdue?: number
    contract_expiring?: number
    inv_value?: number
    out_of_stock?: number
  }
  /** Giá trị NHẬN HÀNG theo tháng của năm đang xem. */
  cost_12m: MonthlyCost[]
  categories: { name: string; cost: number; pct: number }[]
  /** CHI TIÊU theo NCC (tính trên dòng đơn mua) — thuộc khối `purchase_order`. */
  top_suppliers: NamedValue[]
  /** NỢ CÒN LẠI theo NCC — thuộc khối `payable`. Đừng nhầm với `top_suppliers`. */
  top_debt_suppliers: NamedValue[]
  dept_spend: NamedValue[]
  po_status: { key: string; label: string; value: number }[]
  ap_aging: { label: string; value: number }[]
  alerts: DashboardAlert[]
  alert_total: number
  recent_prs: RecentPurchaseRequest[]
  low_stock: LowStockItem[]
  /**
   * Giá trị tồn theo kho (kh-NT2-8) — xếp giảm dần theo `value`, tổng bằng
   * `kpi.inv_value`. Thiếu quyền tồn kho thì mảng rỗng; máy chủ cũ chưa có khóa này
   * nên khai TÙY CHỌN.
   */
  kpi_inv_by_warehouse?: InventoryByWarehouse[]
  can: Record<string, boolean>
}

export const procurementDashboardApi = {
  getOverview: () => apiGet<DashboardOverview>('/api/dashboard/overview'),
}
