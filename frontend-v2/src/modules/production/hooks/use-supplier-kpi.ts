import { useQuery } from '@tanstack/react-query'

import { apiGet } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'

/** Một dòng NCC trong báo cáo ma trận (`report/service.py` — mục "2) NCC"). */
export interface SupplierKpi {
  /**
   * Khóa nhóm là TÊN nhà cung cấp trên đơn (`po.supplier_name`), chỉ khi tên
   * rỗng backend mới rơi về mã. Đây là lý do phải dò theo tên chứ không theo mã.
   */
  key: string
  /** Số lần giao hàng trong kỳ. */
  trans: number
  /** Số lần giao trễ so với ngày quy định. */
  late: number
  /** Tỷ lệ trễ, đã nhân 100 và làm tròn 2 chữ số ở backend. */
  rate: number
  /** Backend bật cờ này khi `rate > 30`. */
  warn: boolean
}

interface MatrixResponse {
  supplier?: SupplierKpi[]
}

/** Cả kỳ, không bó theo năm — điểm đánh giá NCC phải nhìn trọn lịch sử giao dịch. */
const ALL_YEARS = 'all'

/**
 * KPI giao hàng của MỘT nhà cung cấp.
 *
 * Backend không có đường lấy lẻ một NCC: `/api/reports/matrix` trả cả bảng rồi
 * mình dò ra dòng cần. Bù lại khóa cache KHÔNG mang tên NCC nên mở lần lượt
 * mười nhà cung cấp cũng chỉ tải bảng đúng một lần.
 */
export function useSupplierKpi(supplierName: string, options: { enabled?: boolean } = {}) {
  return useQuery({
    queryKey: queryKeys.production.supplierKpi(ALL_YEARS),
    queryFn: () => apiGet<MatrixResponse>('/api/reports/matrix', { params: { year: ALL_YEARS } }),
    // Bảng ma trận là snapshot tính sẵn ở backend, không cần tươi từng phút.
    staleTime: 5 * 60 * 1000,
    enabled: (options.enabled ?? true) && Boolean(supplierName),
    select: (data) => (data.supplier ?? []).find((row) => row.key === supplierName) ?? null,
  })
}
