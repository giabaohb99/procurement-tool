import { useQuery } from '@tanstack/react-query'

import { apiGet } from '@/core/api'

/** Một dòng đếm ngược — khớp `/api/dossier-types/stats` ở backend. */
interface DossierTypeStat {
  type_id: number
  total: number
}

const statsKeys = {
  all: ['dossier', 'dossier-types', 'stats'] as const,
}

/**
 * ĐẾM NGƯỢC: mỗi loại hồ sơ đang có bao nhiêu hồ sơ dùng.
 *
 * ⚠️ Endpoint RIÊNG, cố ý không nhét `dossier_count` vào `DossierTypeResponse`:
 * serializer chạy cho TỪNG dòng nên đếm ở đó là một truy vấn mỗi dòng (N+1, bài
 * học duoc-CR-322), và nó chạy cả ở những chỗ chỉ cần tên loại để đổ ô chọn.
 * Backend gom một truy vấn `GROUP BY` cho cả trang.
 *
 * ⚠️ **Thiếu quyền `dossier.read` thì backend trả RỖNG, không trả 403** —
 * `apply_scope` chặn hết chứ không ném lỗi. Nên nơi dùng phải TỰ TẮT cột, không
 * thì mọi dòng hiện `0` và người đọc tin là chưa hồ sơ nào dùng loại nào. Xem
 * `canCount` ở `dossier-type-crud.tsx`.
 *
 * Trả về `Map` chứ không phải mảng: nơi dùng tra theo id cho từng dòng bảng, mà
 * `.find()` trong ô bảng là quét lại cả danh sách cho mỗi dòng.
 */
export function useDossierTypeStats(enabled: boolean) {
  return useQuery({
    queryKey: statsKeys.all,
    queryFn: async () => {
      const res = await apiGet<{ items: DossierTypeStat[] }>('/api/dossier-types/stats')
      return new Map(res.items.map((row) => [row.type_id, row.total]))
    },
    enabled,
    staleTime: 60 * 1000,
  })
}
