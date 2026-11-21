import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import { toast } from '../../components/toast'
import PackagingHistoryChart from '../../components/packaging/PackagingHistoryChart'
import PackagingHistoryTable from '../../components/packaging/PackagingHistoryTable'
import PackagingHistoryToolbar from '../../components/packaging/PackagingHistoryToolbar'
import { downloadExport, fetchCodeOptions, fetchHhOptions, fetchHistory } from '../../api/packaging-cost'
import type { PackagingCodeOption } from '../../api/packaging-cost-types'
import { useDebouncedValue } from '../../hooks/use-debounced-value'
import { useLatestQuery } from '../../hooks/use-latest-query'
import {
  buildHistoryParams, buildHistorySearch, buildHistorySummary, EMPTY_HISTORY_FILTERS, nextSort,
  parseHistorySearch, sortCodeOptions, type HistoryFilters, type HistorySelection,
} from '../../utils/packaging-query'
import '../../components/packaging/packaging.css'

/**
 * Màn LỊCH SỬ MUA HÀNG: từng lần mua của mã VTBB, hoặc của các thành phần trong định mức của một / nhiều sản phẩm; kèm
 * dòng KPI và biểu đồ "Diễn biến đơn giá" khi chọn đúng một mã. Lịch sử là bản chụp BẤT BIẾN của sổ giá — không có ô sửa
 * đơn giá (sai thì sửa ở ĐMH / nguồn nạp). Lọc + xếp + phân trang tại MÁY CHỦ. Lựa chọn mã nằm ở URL (`?codes=A,B` ·
 * `?hh=HH1,HH2` · `mode`) để các bảng khác dẫn thẳng vào được.
 */
export default function PackagingHistory() {
  const { can } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const selection = useMemo(() => parseHistorySearch(searchParams), [searchParams])
  const [filters, setFilters] = useState<HistoryFilters>(EMPTY_HISTORY_FILTERS)
  const [sortBy, setSortBy] = useState('date')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [exporting, setExporting] = useState(false)
  const [codeOptions, setCodeOptions] = useState<PackagingCodeOption[]>([])
  const [productOptions, setProductOptions] = useState<PackagingCodeOption[]>([])
  const [codesLoading, setCodesLoading] = useState(true)
  const [productsLoading, setProductsLoading] = useState(false)
  const [productsLoaded, setProductsLoaded] = useState(false)
  const q = useDebouncedValue(filters.q, 350)
  const isProduct = selection.mode === 'product'

  useEffect(() => {
    fetchCodeOptions().then((d) => setCodeOptions(sortCodeOptions(d)))
      .catch(() => toast.error('Không nạp được danh sách mã bao bì'))
      .finally(() => setCodesLoading(false))
  }, [])
  //  Danh sách sản phẩm (~1.000) chỉ nạp khi vào chế độ "Theo mã sản phẩm".
  useEffect(() => {
    if (!isProduct || productsLoaded) return
    setProductsLoading(true)
    fetchHhOptions().then((d) => { setProductOptions(d.map((x) => ({ ...x, group: '', usage: 0, new: null }))); setProductsLoaded(true) })
      .catch(() => toast.error('Không nạp được danh sách sản phẩm'))
      .finally(() => setProductsLoading(false))
  }, [isProduct, productsLoaded])

  //  Bấm một mã ngay trên bảng này (hoặc dùng nút Back) đổi URL mà không qua `changeSelection` → cũng về trang 1.
  const urlKey = searchParams.toString()
  useEffect(() => { setPage(1) }, [urlKey])

  /** Bộ lọc + thứ tự gửi máy chủ — dùng chung cho danh sách và Xuất Excel. */
  const filterParams = useMemo(() => buildHistoryParams(selection, filters, q, { by: sortBy, dir: sortDir }), [selection, filters, q, sortBy, sortDir])
  const params = useMemo(() => ({ ...filterParams, page, page_size: pageSize }), [filterParams, page, pageSize])
  const list = useLatestQuery(() => fetchHistory(params), JSON.stringify(params))
  const series = list.data?.series ?? null
  const singleCode = series !== null

  //  Đổi lựa chọn mã / bộ lọc / cột xếp → về trang 1 (đặt cùng lúc với setter để khỏi gọi máy chủ hai lần).
  const changeSelection = (next: HistorySelection) => { setSearchParams(buildHistorySearch(next), { replace: true }); setPage(1) }
  const changeFilters = (next: HistoryFilters) => { setFilters(next); setPage(1) }
  const onSort = (key: string) => { const s = nextSort(sortBy, sortDir, key); setSortBy(s.by); setSortDir(s.dir); setPage(1) }
  const filtersActive = JSON.stringify(filters) !== JSON.stringify(EMPTY_HISTORY_FILTERS)

  async function exportExcel() {
    if (exporting) return
    setExporting(true)
    try { await downloadExport('history', filterParams, 'lich-su-mua-hang.xlsx') }
    catch (e: any) { toast.error(e?.message || 'Không xuất được tệp Excel') }
    finally { setExporting(false) }
  }

  const stats = list.data?.stats
  const summary = stats ? (
    <>
      {buildHistorySummary(stats, singleCode).map((it, i) => (
        <span key={it.label}>{i > 0 && <span style={{ margin: '0 6px' }}>·</span>}{it.label} <b>{it.value}</b></span>
      ))}
      {!singleCode && stats.purchase_count > 0 && (
        <span className="pkg-hint" style={{ marginLeft: 8 }}>(chọn đúng một mã để xem giá bình quân, thấp nhất, cao nhất)</span>
      )}
    </>
  ) : null
  const first = list.data?.items[0]

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 260 }}>
          <h2 className="page-title" style={{ margin: 0 }}>Lịch sử mua hàng</h2>
          <div className="pkg-hint">Từng lần mua của mã vật tư bao bì hoặc của thành phần trong định mức sản phẩm, mới nhất trước. Giá chưa VAT (VND), là bản chụp lúc mua: xanh = đắt hơn lần trước, đỏ = rẻ hơn.</div>
        </div>
        {can('packaging_cost', 'export') && (
          <button className="btn outline" disabled={exporting} onClick={exportExcel}>
            <i className="ti ti-file-spreadsheet" />{exporting ? 'Đang xuất…' : 'Xuất Excel'}
          </button>
        )}
      </div>

      <div className="card pkg-card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <PackagingHistoryToolbar selection={selection} onSelection={changeSelection} filters={filters} onFilters={changeFilters}
          codeOptions={codeOptions} productOptions={productOptions} optionsLoading={isProduct ? productsLoading : codesLoading}
          suppliers={list.data?.suppliers ?? []} />
        {series && series.length > 0 && (
          <PackagingHistoryChart series={series} subject={[first?.code, first?.name].filter(Boolean).join(' · ')} />
        )}
        <PackagingHistoryTable rows={list.data?.items ?? []} total={list.data?.total ?? 0} productMode={isProduct} singleCode={singleCode}
          sortBy={sortBy} sortDir={sortDir} onSort={onSort} page={page} pageSize={pageSize}
          onPage={(p, s) => { setPage(p); setPageSize(s) }} onReload={list.reload} summary={summary}
          empty={list.failed ? 'Không tải được lịch sử — thử tải lại.' : list.loading ? 'Đang tải…'
            : filtersActive ? 'Không có lần mua nào khớp bộ lọc.' : 'Chưa có lần mua nào cho lựa chọn này.'} />
      </div>
    </div>
  )
}
