import { apiGet } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type { SealType } from '../types/seal-type'

const BASE_URL = '/api/seal-types'

/**
 * Danh mục Loại con dấu.
 *
 * Thao tác THÊM / SỬA / XÓA chạy qua lớp CRUD khai báo chung (`@/shared/crud`
 * gọi thẳng `apiPath`), nên ở đây chỉ cần hàm `list` để đổ vào ô chọn trên form
 * tạo phiếu.
 */
export const sealTypeApi = {
  list: (params: ListParams = {}) =>
    apiGet<PaginatedResult<SealType>>(BASE_URL, { params }),
}
