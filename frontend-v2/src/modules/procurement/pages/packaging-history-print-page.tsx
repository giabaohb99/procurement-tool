/**
 * duoc-CR-784 — BẢN IN Lịch sử mua hàng (A4 nằm ngang). Bảng trên màn hình phân trang tại máy chủ nên in màn hình chỉ ra
 * một trang; trang này nhận ĐÚNG bộ lọc qua query string (xem `parseHistoryPrintSearch`) rồi nạp ĐỦ mọi dòng, tới trần
 * `HISTORY_PRINT_ROW_CAP` (quá thì cắt và báo rõ trên tờ giấy).
 *
 * Route đứng NGOÀI khung ứng dụng (như mọi trang in), cổng quyền ở `print-route-access.ts`.
 */
import { useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'

import { extractErrorMessage } from '@/core/api'

import { PackagingPrintShell } from '../components/packaging-print-shell'
import { PrintKpis } from '../components/packaging-print-widgets'
import {
  PrintHistoryFilters,
  PrintHistoryTable,
  PrintPriceChart,
} from '../components/packaging-history-print-parts'
import { usePackagingHistoryPrint } from '../hooks/use-packaging-history-print'
import {
  describeCappedPrint,
  describeHistoryFilters,
  parseHistoryPrintSearch,
} from '../utils/packaging-history-print'
import { buildHistorySummary } from '../utils/packaging-history-summary-items'

export function PackagingHistoryPrintPage() {
  const [searchParams] = useSearchParams()
  const params = useMemo(() => parseHistoryPrintSearch(searchParams), [searchParams])
  const query = usePackagingHistoryPrint(params)
  const data = query.data
  const series = data?.series ?? null
  const singleCode = series !== null
  const productMode = params.mode === 'product'
  const first = data?.items[0]

  const status = query.isError ? 'error' : data ? 'ready' : 'loading'
  const codes = (productMode ? params.hh_codes : params.codes) ?? []
  return (
    <PackagingPrintShell
      subtitle="Lịch sử mua hàng"
      status={status}
      errorMessage={
        query.isError
          ? `Không tải được lịch sử mua hàng: ${extractErrorMessage(query.error)}`
          : undefined
      }
    >
      {data && (
        <>
          <PrintHistoryFilters
            mode={params.mode}
            codes={codes}
            first={first}
            singleCode={singleCode}
            extras={describeHistoryFilters(params, data.suppliers)}
          />
          {data.capped && (
            <p role="status" className="banner">
              {describeCappedPrint(data.total, productMode ? 'dòng' : 'lần mua')}
            </p>
          )}
          <PrintKpis
            items={buildHistorySummary(data.stats, {
              singleCode,
              mode: params.mode,
              selectedCount: codes.length,
            })}
          />
          {series && series.length > 0 && <PrintPriceChart series={series} />}
          <PrintHistoryTable
            rows={data.items}
            productMode={productMode}
            singleCode={singleCode}
            total={data.total}
          />
        </>
      )}
    </PackagingPrintShell>
  )
}
