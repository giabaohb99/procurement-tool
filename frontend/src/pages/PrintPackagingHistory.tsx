import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchAllHistory, printErrorMessage } from '../api/packaging-print'
import type { PackagingHistoryPrintData } from '../api/packaging-print'
import { PrintMultiPriceChart } from '../components/packaging/PackagingHistoryMultiPrintChart'
import { normalizeSeriesByCode } from '../utils/packaging-multi-series-chart'
import { PrintHistoryFilters, PrintHistoryTable, PrintPriceChart } from '../components/packaging/PackagingHistoryPrintParts'
import PackagingPrintShell from '../components/packaging/PackagingPrintShell'
import { PrintKpis } from '../components/packaging/PackagingPrintWidgets'
import { cappedPrintNotice, describeHistoryFilters, parseHistoryPrintSearch } from '../utils/packaging-print'
import { buildHistorySummary } from '../utils/packaging-history-summary'

/**
 * duoc-CR-784 — BẢN IN Lịch sử mua hàng (A4 nằm ngang, bản v1). Bảng trên màn hình phân trang tại máy chủ nên in màn hình chỉ
 * ra một trang; trang này nhận ĐÚNG bộ lọc qua query string (xem `parseHistoryPrintSearch`) rồi nạp ĐỦ mọi dòng, tới trần
 * `PRINT_ROW_CAP` (quá thì cắt và báo rõ trên tờ giấy). Route đứng NGOÀI `AppLayout`, gác bằng `PackagingGate`.
 */
export default function PrintPackagingHistory() {
  const [sp] = useSearchParams()
  const query = sp.toString()
  const params = useMemo(() => parseHistoryPrintSearch(new URLSearchParams(query)), [query])
  const [data, setData] = useState<PackagingHistoryPrintData | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    setData(null); setError('')
    fetchAllHistory(params)
      .then((d) => { if (alive) setData(d) })
      .catch((e) => { if (alive) setError(`Không tải được lịch sử mua hàng: ${printErrorMessage(e)}`) })
    return () => { alive = false }
  }, [params])

  const series = data?.series ?? null
  const seriesByCode = normalizeSeriesByCode(data?.series_by_code)
  const singleCode = series !== null
  const productMode = params.mode === 'product'
  const codes = (productMode ? params.fg_codes : params.codes) ?? []
  return (
    <PackagingPrintShell subtitle="Lịch sử mua hàng" status={error ? 'error' : data ? 'ready' : 'loading'} errorMessage={error}>
      {data && (
        <>
          <PrintHistoryFilters mode={params.mode} codes={codes} first={data.items[0]} singleCode={singleCode}
            extras={describeHistoryFilters(params, data.suppliers)} />
          {data.capped && <p role="status" className="banner">{cappedPrintNotice(data.total, productMode ? 'dòng' : 'lần mua')}</p>}
          <PrintKpis items={buildHistorySummary(data.stats, { singleCode, mode: params.mode, selectedCount: codes.length })} />
          {series && series.length > 0 && <PrintPriceChart series={series} />}
          {seriesByCode.length > 0 && (
            <PrintMultiPriceChart series={seriesByCode} subject={[data.items[0]?.fg_code, data.items[0]?.fg_name].filter(Boolean).join(' · ')} />
          )}
          <PrintHistoryTable rows={data.items} productMode={productMode} singleCode={singleCode} total={data.total} />
        </>
      )}
    </PackagingPrintShell>
  )
}
