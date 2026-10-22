import { useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'

import { queryKeys } from '@/shared/constants/query-keys'
import { orgChartApi } from '../api/org-chart-api'
import { buildOrgChartTree } from '../utils/org-chart-tree'

/** Đọc thẳng dữ liệu mỗi lần mở (không lưu bản vẽ), nên đổi phòng / quản lý là sơ đồ đổi theo. */
export function useOrgChart(options: { enabled?: boolean } = {}) {
  const query = useQuery({
    queryKey: queryKeys.hr.orgChart(),
    queryFn: orgChartApi.get,
    enabled: options.enabled ?? true,
  })
  const tree = useMemo(() => (query.data ? buildOrgChartTree(query.data) : []), [query.data])
  return { ...query, tree }
}
