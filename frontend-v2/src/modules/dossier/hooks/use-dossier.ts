import { useQuery } from '@tanstack/react-query'

import { apiGet } from '@/core/api'
import { usePermission } from '@/core/authorization/use-permission'
import { queryKeys } from '@/shared/constants/query-keys'
import type { Dossier } from '../types/dossier'

/**
 * MỘT tờ hồ sơ đầy đủ.
 *
 * ⚠️ **Có rồi mới gọi, và chỉ gọi khi cần.** Danh sách `applicable` cố ý trả bộ
 * trường gọn (xem `ApplicableDossier`); mấy ô còn lại — ngày cấp, người phụ
 * trách, nơi lưu bản giấy — chỉ hộp sửa mới dùng tới. Nhét chúng vào danh sách
 * là mọi lượt mở phiếu phải cõng thêm dữ liệu mà 99% số lượt không ai nhìn.
 *
 * ⚠️ Tự tắt khi thiếu `dossier.read`, cùng lẽ với `useApplicableDossiers`: thẻ
 * hồ sơ mọc ra ở màn của phân hệ khác, nơi nhiều người không có khóa đó.
 */
export function useDossier(id: number | null) {
  const { can } = usePermission()

  return useQuery({
    queryKey: queryKeys.dossier.detail(id ?? 0),
    queryFn: () => apiGet<Dossier>(`/api/dossiers/${id}`),
    enabled: can('dossier', 'read') && Boolean(id),
  })
}
