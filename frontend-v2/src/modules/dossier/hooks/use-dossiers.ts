import { useQuery } from '@tanstack/react-query'

import { fetchDossiers, type DossierListParams } from '../api/dossier-api'

/**
 * Khóa cục bộ — ngoại lệ được phép của luật "query key nằm ở
 * `shared/constants/query-keys.ts`": khóa này chỉ có một hook dùng và **không ai
 * invalidate từ ngoài** (chưa có thao tác ghi nào trong phân hệ). Có mutation
 * đầu tiên thì dời nó sang bảng khóa tập trung.
 */
const dossierKeys = {
  list: (params: DossierListParams) => ['dossier', 'dossiers', params] as const,
}

/** Một trang danh sách hồ sơ. Dữ liệu còn là MẪU — xem `dossier-api.ts`. */
export function useDossiers(params: DossierListParams) {
  return useQuery({
    queryKey: dossierKeys.list(params),
    queryFn: () => fetchDossiers(params),
  })
}
