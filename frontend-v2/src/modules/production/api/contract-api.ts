import { apiGet } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type { Contract } from '../types/contract'

const BASE_URL = '/api/contracts'

/**
 * Hợp đồng — hiện mới dùng ở tab "Hợp đồng" của trang chi tiết NCC nên chỉ có
 * phần ĐỌC. Màn danh mục Hợp đồng đầy đủ (Đ-04) sẽ bổ sung create/update/delete.
 *
 * Whitelist lọc của backend (`FILTERABLE`): code · party_type · party_code ·
 * party_name · status · contract_type · title · end_date. Ngoài ra controller tự
 * đọc `signed` và `expiry`.
 */
export const contractApi = {
  list: (params: ListParams) => apiGet<PaginatedResult<Contract>>(BASE_URL, { params }),
}
