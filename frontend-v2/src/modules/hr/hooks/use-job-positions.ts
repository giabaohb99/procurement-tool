import { useQuery } from '@tanstack/react-query'

import { apiGet } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'
import type { PaginatedResult } from '@/shared/types/api'
import type { JobPosition } from '../types/job-position'

/**
 * Danh mục CHỨC VỤ để đổ vào ô chọn «Vị trí / Chức vụ» (duoc-CR-320).
 *
 * Lấy MỘT lượt 500 dòng thay vì tìm động: một công ty có vài chục chức vụ, và ô
 * chọn phải mở ra là thấy đủ. Cùng cách đang dùng cho ô chọn phòng ban và ô chọn
 * người quản lý trực tiếp ở màn hồ sơ.
 *
 * ⚠️ Chỉ lấy dòng **đang dùng**: chức vụ đã ngừng không được gán MỚI (backend
 * chặn), nên bày ra là mời người dùng bấm vào một mục sẽ bị từ chối. Hồ sơ đang
 * giữ một chức vụ đã ngừng vẫn hiện đúng tên nhờ `fallbackLabel` của
 * `LookupSelect` — và vẫn lưu được vì backend cho giữ nguyên giá trị cũ.
 *
 * ⚠️ Sắp theo **TÊN**, khai rõ ở đây chứ đừng bỏ trống: mặc định của
 * `make_crud_router` là `id desc`, tức ô chọn đổ ra theo thứ tự NGƯỜI TA GÕ
 * VÀO — chức vụ thêm sau cùng nằm trên đầu, và cùng một danh sách đổi chỗ mỗi
 * lần có người thêm một dòng. Cột `sort_order` cố ý KHÔNG dùng để sắp (xem
 * docstring của `job-position-crud.tsx`).
 */
export function useJobPositions(enabled = true) {
  const params = { page_size: 500, is_active: true, sort_by: 'name', sort_dir: 'asc' }

  return useQuery({
    queryKey: queryKeys.hr.jobPositions(params),
    queryFn: () => apiGet<PaginatedResult<JobPosition>>('/api/job-positions', { params }),
    enabled,
  })
}
