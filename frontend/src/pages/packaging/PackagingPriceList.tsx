import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../../auth/AuthContext'
import DateRangePicker from '../../components/DateRangePicker'
import Pagination from '../../components/Pagination'
import TableHead, { TableCells, TableColGroup } from '../../components/TableHead'
import TableScroll from '../../components/TableScroll'
import TableCards from '../../components/TableCards'
import { useNarrowScreen } from '../../hooks/useNarrowScreen'
import TableToolbar from '../../components/TableToolbar'
import { toast } from '../../components/toast'
import PackagingExcelImportButton from '../../components/packaging/PackagingExcelImportButton'
import PackagingQuoteModal from '../../components/packaging/PackagingQuoteModal'
import { CodeLink, DiffText, Dash, OneLine, PctText, PriceText } from '../../components/packaging/PackagingCells'
import { IMPORT_MODULE_PACKAGING_QUOTE, downloadExport, fetchCodeOptions, fetchPriceList } from '../../api/packaging-cost'
import type { PackagingPriceListParams, PackagingPriceRow } from '../../api/packaging-cost-types'
import { useDebouncedValue } from '../../hooks/use-debounced-value'
import { useLatestQuery } from '../../hooks/use-latest-query'
import { useTableColumns, TableColumn } from '../../hooks/useTableColumns'
import { fmtDateStr } from '../../utils/datetime'
import { joinWarnings } from '../../utils/packaging-price'
import { collectGroups, nextSort } from '../../utils/packaging-query'
import { PRICE_LIST_URL_KEYS, priceListScreenToSearch, searchToPriceListScreen } from '../../utils/packaging-prices-screen-url'
import { useSearchSyncToUrl } from '../../hooks/useSearchSyncToUrl'
import '../../components/packaging/packaging.css'

interface Filters { q: string; group: string; scope: 'bom' | 'all' }
const EMPTY: Filters = { q: '', group: '', scope: 'bom' }

/**
 * Màn BẢNG GIÁ VTBB: mỗi mã một dòng với số lần mua, hai lần mua gần nhất, báo giá mới nhất, giá cũ / mới, min–max theo
 * khoảng ngày và số sản phẩm đang dùng. Phân trang + xếp tại MÁY CHỦ — tham số xếp đi kèm bộ lọc nên
 * Xuất Excel ra đúng thứ tự đang xem. Nút từng dòng: Báo giá.
 */
export default function PackagingPriceList() {
  const { can } = useAuth()
  //  Trạng thái ban đầu đọc từ URL (F5 / link được chia sẻ vẫn giữ từ khóa, nhóm, phạm vi, khoảng ngày, cột xếp, trang).
  const [initial] = useState(() => searchToPriceListScreen(window.location.search))
  const [filters, setFilters] = useState<Filters>({ q: initial.q, group: initial.group, scope: initial.scope })
  const [range, setRange] = useState(initial.range)
  const [sortBy, setSortBy] = useState(initial.sortBy)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>(initial.sortDir)
  const [page, setPage] = useState(initial.page)
  const [pageSize, setPageSize] = useState(initial.pageSize)
  const [groups, setGroups] = useState<string[]>([])
  const [quoteCode, setQuoteCode] = useState<string | null>(null)   // '' = mở "Báo giá mới" chưa khóa mã
  const [exporting, setExporting] = useState(false)
  const q = useDebouncedValue(filters.q, 350).trim()
  const canQuote = can('packaging_cost', 'create')

  //  Nhóm cho chip lấy từ mã đang dùng trong định mức.
  useEffect(() => { fetchCodeOptions().then((d) => setGroups(collectGroups(d))).catch(() => {}) }, [])

  /** Bộ lọc + thứ tự gửi máy chủ — dùng chung cho danh sách và Xuất Excel. */
  const filterParams = useMemo<PackagingPriceListParams>(() => ({
    q: q || undefined,
    group: filters.group || undefined,
    scope: filters.scope,
    date_from: range.from || undefined,
    date_to: range.to || undefined,
    ...(sortBy ? { sort_by: sortBy, sort_dir: sortDir } : {}),
  }), [q, filters.group, filters.scope, range, sortBy, sortDir])
  const params = useMemo(() => ({ ...filterParams, page, page_size: pageSize }), [filterParams, page, pageSize])
  const list = useLatestQuery(() => fetchPriceList(params), JSON.stringify(params))

  const urlSearch = useMemo(
    () => priceListScreenToSearch({ ...filters, range, sortBy, sortDir, page, pageSize }),
    [filters, range, sortBy, sortDir, page, pageSize])
  useSearchSyncToUrl(urlSearch, PRICE_LIST_URL_KEYS)
  //  Trang từ URL (hoặc sau khi lọc ra ít dòng) vượt số trang thật thì lùi về trang cuối.
  const listTotal = list.data?.total
  useEffect(() => {
    if (listTotal == null) return
    const last = Math.max(1, Math.ceil(listTotal / pageSize))
    if (page > last) setPage(last)
  }, [listTotal, pageSize, page])

  //  Đổi bộ lọc / cột xếp → về trang 1 (đặt cùng lúc với setter để khỏi gọi máy chủ hai lần).
  const patch = (next: Partial<Filters>) => { setFilters((f) => ({ ...f, ...next })); setPage(1) }
  const filtersActive = JSON.stringify(filters) !== JSON.stringify(EMPTY) || !!(range.from || range.to)
  const clearFilters = () => { setFilters(EMPTY); setRange({ from: '', to: '' }); setPage(1) }
  const onSort = (key: string) => { const s = nextSort(sortBy, sortDir, key); setSortBy(s.by); setSortDir(s.dir); setPage(1) }

  const columns = useMemo<TableColumn<PackagingPriceRow>[]>(() => [
    { key: 'code', label: 'Mã VTBB', width: 120, sort: 'code', fixed: true, card: 'title', cell: (r) => <CodeLink code={r.code} /> },
    { key: 'name', label: 'Tên vật tư', width: 250, sort: 'name', card: 'subtitle', cell: (r) => (r.name ? <OneLine>{r.name}</OneLine> : <span className="pkg-muted">(chưa có tên)</span>) },
    { key: 'group', label: 'Nhóm', width: 90, sort: 'group', cell: (r) => r.group },
    { key: 'unit', label: 'ĐVT', width: 70, cell: (r) => r.unit },
    { key: 'purchase_count', label: 'Số lần mua', width: 90, align: 'right', sort: 'purchase_count', cell: (r) => r.purchase_count },
    { key: 'last_date', label: 'Mua gần nhất', width: 110, sort: 'last_date', cell: (r) => (r.last_date ? fmtDateStr(r.last_date) : <Dash />) },
    { key: 'last_purchase_price', label: 'Giá mua gần nhất', width: 120, align: 'right', sort: 'last_purchase_price', cell: (r) => <PriceText value={r.last_purchase_price} /> },
    { key: 'prev_purchase_price', label: 'Giá mua lần trước', width: 120, align: 'right', sort: 'prev_purchase_price', cell: (r) => <PriceText value={r.prev_purchase_price} /> },
    {
      key: 'quote', label: 'Báo giá mới', width: 120, align: 'right', sort: 'quote_price',
      cell: (r) => (r.quote ? (
        <div style={{ lineHeight: 1.25 }}>
          <PriceText value={r.quote.price} />
          <div className="pkg-hint">{fmtDateStr(r.quote.valid_from)}</div>
        </div>
      ) : <Dash />),
    },
    { key: 'old', label: 'Giá cũ', width: 100, align: 'right', sort: 'old', card: 'hero', cell: (r) => <PriceText value={r.old} bold /> },
    { key: 'new', label: 'Giá mới', width: 100, align: 'right', sort: 'new', card: 'hero', cell: (r) => <PriceText value={r.new} bold /> },
    { key: 'diff', label: 'Chênh lệch', width: 100, align: 'right', sort: 'diff', card: 'hero', cell: (r) => <DiffText value={r.diff} /> },
    { key: 'pct', label: '%', width: 80, align: 'right', sort: 'pct', card: 'hero', cell: (r) => <PctText value={r.pct} /> },
    //  Min và Max tách hai cột, mỗi cột xếp theo đúng giá trị nó hiện.
    { key: 'min', label: 'Min', width: 100, align: 'right', sort: 'min', cell: (r) => <PriceText value={r.min} /> },
    { key: 'max', label: 'Max', width: 100, align: 'right', sort: 'max', cell: (r) => <PriceText value={r.max} /> },
    { key: 'usage', label: 'Số SP đang dùng', width: 100, align: 'right', sort: 'usage', cell: (r) => r.usage },
    { key: 'note', label: 'Ghi chú', width: 200, defaultHidden: true, card: 'full', cell: (r) => (joinWarnings(r.warnings) ? <span className="pkg-err">{joinWarnings(r.warnings)}</span> : null) },
    {
      key: 'actions', label: 'Thao tác', width: 170, fixed: true, card: 'action',
      cell: (r) => (
        <span className="pkg-actions">
          {canQuote && <button className="btn outline sm" onClick={() => setQuoteCode(r.code)}>Báo giá</button>}
        </span>
      ),
    },
  ], [canQuote])
  const table = useTableColumns('packaging-price-list', columns)
  const minW = table.columns.reduce((s, c) => s + (typeof c.width === 'number' ? c.width : 100), 0)
  const rows = list.data?.items ?? []
  const narrow = useNarrowScreen()
  const emptyText = list.failed ? 'Không tải được bảng giá — thử tải lại.' : list.loading ? 'Đang tải…'
    : filtersActive ? 'Không có mã nào khớp bộ lọc.' : 'Chưa có mã vật tư bao bì nào trong định mức.'

  async function exportExcel() {
    if (exporting) return
    setExporting(true)
    try { await downloadExport('price-list', filterParams, 'bang-gia-vtbb.xlsx') }
    catch (e: any) { toast.error(e?.message || 'Không xuất được tệp Excel') }
    finally { setExporting(false) }
  }

  return (
    <div>
      <div className="pkg-head" style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 260 }}>
          <h2 className="page-title" style={{ margin: 0 }}>Bảng giá VTBB</h2>
          <div className="pkg-hint">Giá cũ / mới từng mã vật tư bao bì: có báo giá thì giá mới là báo giá, không thì là lần mua gần nhất. Đơn vị VNĐ, chưa VAT.</div>
        </div>
        <div style={{ width: 280 }}>
          <DateRangePicker block value={range} placeholder="Khoảng ngày tính min – max"
            onChange={(v) => { setRange(v); setPage(1) }} />
        </div>
        {canQuote && <button className="btn" title="Báo giá mới" aria-label="Báo giá mới" onClick={() => setQuoteCode('')}><i className="ti ti-plus" /><span className="pkg-btn-label">Báo giá mới</span></button>}
        <PackagingExcelImportButton module={IMPORT_MODULE_PACKAGING_QUOTE} action="create"
          label="Nhập báo giá" title="Nhập báo giá VTBB từ Excel"
          description="Mỗi dòng một báo giá: Mã VTBB, Đơn giá (VNĐ chưa VAT), Ngày hiệu lực; tùy chọn Mã NCC, VAT (%), Ghi chú. Trùng mã + NCC + ngày hiệu lực thì cập nhật, chưa có thì thêm. Chạy thử trước, xem nhật ký rồi bấm Ghi thật." />
        {can('packaging_cost', 'export') && (
          <button className="btn outline" disabled={exporting} onClick={exportExcel} title="Xuất Excel" aria-label="Xuất Excel">
            <i className="ti ti-file-spreadsheet" /><span className="pkg-btn-label">{exporting ? 'Đang xuất…' : 'Xuất Excel'}</span>
          </button>
        )}
      </div>

      <div className="card table-card">
        {/* Thanh lọc nằm CÙNG hàng với nút Tải lại / Cột của bảng (người chủ báo dải trống giữa hai hàng, 23/11/2026). */}
        <TableToolbar compact {...table} onRefresh={list.reload}>
          <div className="pkg-row" style={{ flex: 1, minWidth: 0 }}>
            <div className="pkg-search">
              <input aria-label="Tìm mã vật tư" placeholder="Tìm mã, tên vật tư…" value={filters.q} onChange={(e) => patch({ q: e.target.value })} />
            </div>
            <div className="pkg-pills" role="group" aria-label="Lọc theo nhóm">
              {['', ...groups].map((g) => (
                <button key={g || 'all'} type="button" className={'pkg-pill' + (filters.group === g ? ' on' : '')}
                  aria-pressed={filters.group === g} onClick={() => patch({ group: g })}>{g || 'Tất cả'}</button>
              ))}
            </div>
            <div className="pkg-seg" role="group" aria-label="Phạm vi mã">
              <button className={filters.scope === 'bom' ? 'on' : ''} onClick={() => patch({ scope: 'bom' })}>Mã trong định mức</button>
              <button className={filters.scope === 'all' ? 'on' : ''} onClick={() => patch({ scope: 'all' })}>Mọi mã có giá</button>
            </div>
            {filtersActive && <button className="btn ghost sm" onClick={clearFilters}><i className="ti ti-rotate" />Xóa lọc</button>}
          </div>
        </TableToolbar>
        {narrow ? (
          <TableCards columns={table.columns} rows={rows} rowKey={(r) => r.code} sortBy={sortBy} sortDir={sortDir} onSort={onSort}
            empty={emptyText} />
        ) : (
        <TableScroll>
          <table className="dense" style={{ minWidth: minW, tableLayout: 'fixed' }}>
            <TableColGroup columns={table.columns} colW={table.colW} />
            <TableHead columns={table.columns} startResize={table.startResize} sortBy={sortBy} sortDir={sortDir} onSort={onSort} />
            <tbody>
              {rows.map((r, i) => <tr key={r.code}><TableCells columns={table.columns} row={r} index={i} /></tr>)}
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

      {quoteCode !== null && (
        <PackagingQuoteModal defaultCode={quoteCode || undefined} onClose={() => setQuoteCode(null)} onSaved={list.reload} />
      )}
    </div>
  )
}
