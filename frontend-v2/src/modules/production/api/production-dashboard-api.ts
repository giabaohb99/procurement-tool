import { apiGet } from '@/core/api'

/** Một phân loại VTBB kèm số sản phẩm thuộc nó. */
export interface ProductGroupCount {
  name: string
  value: number
}

/** Một hợp đồng sắp tới hạn — đủ để hiện dòng cảnh báo và bấm sang chi tiết. */
export interface ExpiringContract {
  id: number
  code: string
  title: string
  /** Tên đối tượng ký; backend đã rơi về mã khi tên rỗng. */
  party_name: string
  end_date: string
}

/**
 * `GET /api/dashboard/production` — số liệu trang Tổng quan Sản xuất trong MỘT
 * lần gọi, đã lọc theo phạm vi dữ liệu của người đang đăng nhập.
 *
 * Giống hệt luật của `/api/dashboard/overview`: route chỉ đòi đăng nhập rồi gác
 * TỪNG KHỐI bằng quyền Xem của entity tương ứng, khối bị gác thì **khóa biến
 * mất** chứ không trả `0`. Nên mọi khóa trong `kpi` đều tùy chọn — luôn đọc kèm
 * `?? 0`, và hỏi `can` khi muốn biết "không có dòng nào" hay "không được xem".
 */
export interface ProductionOverview {
  kpi: {
    /** Khối `supplier`. */
    supplier_total?: number
    supplier_goods?: number
    supplier_transport?: number
    supplier_inactive?: number
    /** Khối `product`. */
    product_total?: number
    product_inactive?: number
    /** Khối `unit` / `item_group`. */
    unit_total?: number
    item_group_total?: number
    /** Khối `contract`. `contract_live` = chưa thanh lý, chưa hủy. */
    contract_total?: number
    contract_live?: number
    contract_expiring?: number
    contract_expired?: number
    contract_unsigned?: number
  }
  /** Sản phẩm theo phân loại: 6 nhóm lớn nhất, phần đuôi gộp thành "Khác". */
  product_groups: ProductGroupCount[]
  /** 8 hợp đồng hết hạn gần nhất trong 30 ngày tới, xếp theo hạn tăng dần. */
  expiring_contracts: ExpiringContract[]
  can: {
    supplier: boolean
    product: boolean
    unit: boolean
    item_group: boolean
    contract: boolean
  }
}

export const productionDashboardApi = {
  getOverview: () => apiGet<ProductionOverview>('/api/dashboard/production'),
}
