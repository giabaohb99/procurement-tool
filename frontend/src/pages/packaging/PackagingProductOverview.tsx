import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../../auth/AuthContext'
import Pagination from '../../components/Pagination'
import TableHead, { TableCells, TableColGroup } from '../../components/TableHead'
import TableToolbar from '../../components/TableToolbar'
import TableScroll from '../../components/TableScroll'
import TableCards from '../../components/TableCards'
import { ProductCard } from '../../components/packaging/PackagingMobileCards'
import { useNarrowScreen } from '../../hooks/useNarrowScreen'
import { toast } from '../../components/toast'
import { PctText, TrendText } from '../../components/packaging/PackagingCells'
import PackagingOverviewToolbar from '../../components/packaging/PackagingOverviewToolbar'
import { buildProductColumns } from '../../components/packaging/PackagingProductColumns'
import { PACKAGING_ENTITY, downloadExport, fetchProductOverview } from '../../api/packaging-cost'
import type { PackagingImpactProduct, PackagingOverviewTrend } from '../../api/packaging-cost-types'
import { useDebouncedValue } from '../../hooks/use-debounced-value'
import { useLatestQuery } from '../../hooks/use-latest-query'
import { useTableColumns, type TableColumn } from '../../hooks/useTableColumns'
import { EMPTY_IMPACT_FILTERS, countAdvancedFilters } from '../../utils/packaging-impact-filters'
import type { ImpactAdvancedFilters } from '../../utils/packaging-impact-filters'
import { buildOverviewParams } from '../../utils/packaging-overview'
import { nextSort } from '../../utils/packaging-query'
import { OVERVIEW_URL_KEYS, overviewScreenToSearch, searchToOverviewScreen } from '../../utils/packaging-screen-url'
import { useSearchSyncToUrl } from '../../hooks/useSearchSyncToUrl'
import '../../components/packaging/packaging.css'

/** "% chênh" và "Xu hướng" đứng ngay sau các cột chi phí — Tác động giá không có. */
const EXTRA_COLUMNS: TableColumn<PackagingImpactProduct>[] = [
  { key: 'pct', label: '% chênh', width: 80, align: 'right', sort: 'pct', card: 'field', cell: (r) => <PctText value={r.pct} /> },
  { key: 'trend', label: 'Xu hướng', width: 96, card: 'field', cell: (r) => <TrendText trend={r.trend} /> },
]

/**
 * Màn TỔNG HỢP THEO SẢN PHẨM (bám tab "Tổng hợp" của bản mẫu): mọi sản phẩm có định mức bao bì với chi phí bao bì / chai
 * cũ so với mới và xu hướng — Tăng (cần xem lại giá bán) · Giảm · Không đổi · Chưa có giá (thiếu giá chai). Cùng công
 * thức và luật giá cũ / mới với Tác động giá, nhưng không có giá giả định. Lọc + xếp + phân trang tại MÁY CHỦ; tham số
 * đi kèm Xuất Excel để ra đúng thứ tự.
 */
export default function PackagingProductOverview() {
  const { can } = useAuth()
  //  Trạng thái ban đầu đọc từ URL (F5 / link được chia sẻ vẫn giữ từ khóa, xu hướng, chip lọc, xếp, trang).
  const [initial] = useState(() => searchToOverviewScreen(window.location.search))
  const [keyword, setKeyword] = useState(initial.keyword)
  const [trend, setTrend] = useState<PackagingOverviewTrend>(initial.trend)
  const [advanced, setAdvanced] = useState<ImpactAdvancedFilters>(initial.filters)
  const [sortBy, setSortBy] = useState(initial.sortBy)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>(initial.sortDir)
  const [page, setPage] = useState(initial.page)
  const [pageSize, setPageSize] = useState(initial.pageSize)
  const [exporting, setExporting] = useState(false)
  const q = useDebouncedValue(keyword, 350)

  /** Bộ lọc + thứ tự gửi máy chủ — dùng chung cho danh sách và Xuất Excel. */
  const filterParams = useMemo(
    () => buildOverviewParams(trend, q, { by: sortBy, dir: sortDir }, advanced), [trend, q, sortBy, sortDir, advanced])
  const params = useMemo(() => ({ ...filterParams, page, page_size: pageSize }), [filterParams, page, pageSize])
  const list = useLatestQuery(() => fetchProductOverview(params), JSON.stringify(params))

  const urlSearch = useMemo(
    () => overviewScreenToSearch({ keyword, trend, filters: advanced, sortBy, sortDir, page, pageSize }),
    [keyword, trend, advanced, sortBy, sortDir, page, pageSize])
  useSearchSyncToUrl(urlSearch, OVERVIEW_URL_KEYS)

  //  Trang từ URL (hoặc sau khi lọc ra ít dòng) vượt số trang thật thì lùi về trang cuối.
  const listTotal = list.data?.total
  useEffect(() => {
    if (listTotal == null) return
    const last = Math.max(1, Math.ceil(listTotal / pageSize))
    if (page > last) setPage(last)
  }, [listTotal, pageSize, page])

  const offset = (page - 1) * pageSize
  const columns = useMemo(
    () => buildProductColumns({ offset, newKey: 'cost_new_bottle', compact: true, extraAfterCosts: EXTRA_COLUMNS }), [offset])
  const table = useTableColumns('packaging-product-overview', columns)
  const minW = table.columns.reduce((s, c) => s + (typeof c.width === 'number' ? c.width : 100), 0)

  const filtersActive = trend !== 'all' || keyword.trim() !== '' || countAdvancedFilters(advanced, 'overview') > 0
  const reset = () => { setKeyword(''); setTrend('all'); setAdvanced(EMPTY_IMPACT_FILTERS); setPage(1) }
  const onSort = (key: string) => { const s = nextSort(sortBy, sortDir, key); setSortBy(s.by); setSortDir(s.dir); setPage(1) }

  async function exportExcel() {
    if (exporting) return
    setExporting(true)
    try { await downloadExport('product-overview', filterParams, 'tong-hop-theo-san-pham.xlsx') }
    catch (e: any) { toast.error(e?.message || 'Không xuất được tệp Excel') }
    finally { setExporting(false) }
  }

  const rows = list.data?.items ?? []
  const narrow = useNarrowScreen()
  const emptyText = list.failed ? 'Không tải được dữ liệu — thử tải lại.' : list.loading ? 'Đang tải…'
    : filtersActive ? 'Không có sản phẩm nào khớp bộ lọc.' : 'Chưa có sản phẩm nào có định mức bao bì.'
  return (
    <div>
      <div className="pkg-head" style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 260 }}>
          <h2 className="page-title" style={{ margin: 0 }}>Tổng hợp theo sản phẩm</h2>
          <div className="pkg-hint">Chi phí bao bì / chai của mọi sản phẩm có định mức, giá cũ so với giá mới (báo giá hoặc lần mua gần nhất). Sản phẩm tăng chi phí là sản phẩm cần xem lại giá bán; thiếu giá chai thì chưa tính được. Đơn vị VNĐ, chưa VAT.</div>
        </div>
        {can(PACKAGING_ENTITY.products, 'export') && (
          <button className="btn outline" disabled={exporting} onClick={exportExcel} title="Xuất Excel" aria-label="Xuất Excel">
            <i className="ti ti-file-spreadsheet" /><span className="pkg-btn-label">{exporting ? 'Đang xuất…' : 'Xuất Excel'}</span>
          </button>
        )}
      </div>

      <div className="card table-card">
        {/* Thanh lọc nằm CÙNG hàng với nút Cột / Tải lại của bảng (người chủ báo dải trống giữa hai hàng, 25/11/2026). */}
        <TableToolbar compact {...table} onRefresh={list.reload}>
          <PackagingOverviewToolbar keyword={keyword} onKeyword={(v) => { setKeyword(v); setPage(1) }}
            trend={trend} onTrend={(v) => { setTrend(v); setPage(1) }} counts={list.data?.counts}
            advanced={advanced} onAdvanced={(v) => { setAdvanced(v); setPage(1) }}
            filtersActive={filtersActive} onReset={reset} />
        </TableToolbar>
        {narrow ? (
          <TableCards columns={table.columns} rows={rows} rowKey={(r) => r.fg_code} sortBy={sortBy} sortDir={sortDir} onSort={onSort}
            empty={emptyText} renderCard={(r) => <ProductCard row={r} overview />} />
        ) : (
        <TableScroll>
          <table className="dense" style={{ minWidth: minW, tableLayout: 'fixed' }}>
            <TableColGroup columns={table.columns} colW={table.colW} />
            <TableHead columns={table.columns} startResize={table.startResize} sortBy={sortBy} sortDir={sortDir} onSort={onSort} />
            <tbody>
              {rows.map((r, i) => <tr key={r.fg_code}><TableCells columns={table.columns} row={r} index={i} /></tr>)}
              {rows.length === 0 && (
                <tr><td colSpan={table.columns.length} className="table-empty">{emptyText}</td></tr>
              )}
            </tbody>
          </table>
        </TableScroll>
        )}
        <div className="table-foot">
          <Pagination page={page} pageSize={pageSize} total={list.data?.total ?? 0} onChange={(p, s) => { setPage(p); setPageSize(s) }} />
        </div>
      </div>
    </div>
  )
}
