import { useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'

import { useSetUrlParams } from '@/shared/hooks/use-url-param-state'

import {
  buildFlexibleChartUrlPatch,
  FLEXIBLE_CHART_URL_PARAMS,
  resolveFlexibleChartOptions,
  type FlexibleChartContext,
  type FlexibleChartOptions,
} from '../utils/report-flexible-chart-options'

/**
 * Lựa chọn của biểu đồ linh hoạt, lấy URL làm nguồn sự thật (`chart_by`, `chart_type`,
 * `chart_top`). `setOptions` ghi CẢ BA trong MỘT lượt `setParams` — đổi «Vẽ theo» kéo theo
 * đổi kiểu, hai lượt ghi liên tiếp thì lượt sau đọc URL cũ và đè mất lượt trước
 * (`use-url-param-state.ts`).
 */
export function useReportFlexibleChartOptions(ctx: FlexibleChartContext) {
  const [searchParams] = useSearchParams()
  const setParams = useSetUrlParams()
  const rawBy = searchParams.get(FLEXIBLE_CHART_URL_PARAMS.by)
  const rawType = searchParams.get(FLEXIBLE_CHART_URL_PARAMS.type)
  const rawTop = searchParams.get(FLEXIBLE_CHART_URL_PARAMS.top)
  const { hasTime, hasGroup, preferGroup, donutAllowed } = ctx

  const options = useMemo(
    () =>
      resolveFlexibleChartOptions(
        { by: rawBy, type: rawType, top: rawTop },
        { hasTime, hasGroup, preferGroup, donutAllowed },
      ),
    [rawBy, rawType, rawTop, hasTime, hasGroup, preferGroup, donutAllowed],
  )

  const setOptions = useCallback(
    (patch: Partial<FlexibleChartOptions>) =>
      setParams(
        buildFlexibleChartUrlPatch(options, patch, { hasTime, hasGroup, preferGroup, donutAllowed }),
      ),
    [options, setParams, hasTime, hasGroup, preferGroup, donutAllowed],
  )

  return { options, setOptions }
}
