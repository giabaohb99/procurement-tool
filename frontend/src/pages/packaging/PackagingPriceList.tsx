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
import {
  IMPORT_MODULE_PACKAGING_QUOTE, PACKAGING_ENTITY, downloadExport, fetchCodeOptions, fetchPriceList, type PackagingEntity,
} from '../../api/packaging-cost'
import type { PackagingCodeOption, PackagingPriceListParams, PackagingPriceRow } from '../../api/packaging-cost-types'
import { useLatestQuery } from '../../hooks/use-latest-query'
import { useTableColumns, TableColumn } from '../../hooks/useTableColumns'
import { fmtDateStr } from '../../utils/datetime'
import { joinWarnings } from '../../utils/packaging-price'
import { collectGroups, nextSort, sortCodeOptions } from '../../utils/packaging-query'
import PackagingCodePicker, { type PackagingPickerKind } from '../../components/packaging/PackagingCodePicker'
import { PRICE_LIST_URL_KEYS, priceListScreenToSearch, searchToPriceListScreen } from '../../utils/packaging-prices-screen-url'
import { useSearchSyncToUrl } from '../../hooks/useSearchSyncToUrl'
import '../../components/packaging/packaging.css'

interface Filters { codes: string[]; group: string; scope: 'bom' | 'all' }
const EMPTY: Filters = { codes: [], group: '', scope: 'bom' }

/**
 * bao-CR-800 — NGUỒN DỮ LIỆU + chữ của một màn bảng giá. Hai màn Bảng giá VTBB và Bảng giá nguyên liệu dùng CHUNG khung
 * (`PackagingPriceListScreen`), chỉ khác bộ này: mỗi màn gọi đường riêng và hỏi khóa quyền riêng của mình, không gọi chéo.
 */
export interface PriceListSource {
  /** Khóa quyền của màn: `export` cho nút Xuất Excel, `create` cho Báo giá (chỉ khi `packaging`). */
  entity: PackagingEntity
  /**
   * Phần CHỈ CÓ ở Bảng giá VTBB: nút phạm vi (Mã trong định mức / Mọi mã có giá), cột Số SP đang dùng + Ghi chú, mã bấm
   * sang Lịch sử mua hàng, Báo giá (nút đầu trang, cột Thao tác, Nhập báo giá). Màn nguyên liệu tắt hết: mã là chữ thường.
   */
  packaging: boolean
  /** Khóa lưu cấu hình cột của bảng (`useTableColumns`). */
  tableKey: string
  title: string
  hint: string
  codeLabel: string
  nameLabel: string
  pickerKind: PackagingPickerKind
  pickerPlaceholder: string
  /** Câu khi bảng rỗng mà KHÔNG lọc gì. */
  emptyText: string
  exportPath: 'price-list' | 'material-price-list'
  exportName: string
  fetchList: (params: PackagingPriceListParams) => Promise<{ items: PackagingPriceRow[]; total: number }>
  fetchCodes: () => Promise<PackagingCodeOption[]>
}

const PACKAGING_SOURCE: PriceListSource = {
  entity: PACKAGING_ENTITY.priceList,
  packaging: true,
  tableKey: 'packaging-price-list',
  title: 'Bảng giá VTBB',
  hint: 'Giá cũ / mới từng mã vật tư bao bì: có báo giá thì giá mới là báo giá, không thì là lần mua gần nhất. Đơn vị VNĐ, chưa VAT.',
  codeLabel: 'Mã VTBB',
  nameLabel: 'Tên vật tư',
  pickerKind: 'material',
  pickerPlaceholder: 'Tìm mã VTBB — gõ mã, tên, nhóm hoặc NCC, chọn được nhiều mã',
  emptyText: 'Chưa có mã vật tư bao bì nào trong định mức.',
  exportPath: 'price-list',
  exportName: 'bang-gia-vtbb.xlsx',
  fetchList: fetchPriceList,
  //  Ô chọn mã (27/11/2026): mọi mã có trong sổ giá.
  fetchCodes: () => fetchCodeOptions('all'),
}

/**
 * Màn BẢNG GIÁ VTBB: mỗi mã một dòng với số lần mua, hai lần mua gần nhất, báo giá mới nhất, giá cũ / mới, min–max theo
 * khoảng ngày và số sản phẩm đang dùng. Phân trang + xếp tại MÁY CHỦ — tham số xếp đi kèm bộ lọc nên
 * Xuất Excel ra đúng thứ tự đang xem. Nút từng dòng: Báo giá.
 */
export default function PackagingPriceList() {
  return <PackagingPriceListScreen source={PACKAGING_SOURCE} />
}

/** Khung chung của hai màn bảng giá (VTBB / nguyên liệu, bao-CR-800) — `source` quyết định đường gọi, khóa quyền và phần riêng của VTBB. */
export function PackagingPriceListScreen({ source }: { source: PriceListSource }) {
  const { can } = useAuth()
  const { packaging } = source
  //  Trạng thái ban đầu đọc từ URL (F5 / link được chia sẻ vẫn giữ từ khóa, nhóm, phạm vi, khoảng ngày, cột xếp, trang).
  const [initial] = useState(() => {
    const st = searchToPriceListScreen(window.location.search)
    //  Màn nguyên liệu không có phạm vi mã và không có cột Số SP đang dùng: bỏ `scope` / khóa xếp `usage` lạc trên URL.
    return packaging ? st : { ...st, scope: EMPTY.scope, sortBy: st.sortBy === 'usage' ? '' : st.sortBy }
  })
  const [filters, setFilters] = useState<Filters>({ codes: initial.codes, group: initial.group, scope: initial.scope })
  const [range, setRange] = useState(initial.range)
  const [sortBy, setSortBy] = useState(initial.sortBy)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>(initial.sortDir)
  const [page, setPage] = useState(initial.page)
  const [pageSize, setPageSize] = useState(initial.pageSize)
  const [groups, setGroups] = useState<string[]>([])
  const [codeOptions, setCodeOptions] = useState<PackagingCodeOption[]>([])
  const [codesLoading, setCodesLoading] = useState(true)
  const [quoteCode, setQuoteCode] = useState<string | null>(null)   // '' = mở "Báo giá mới" chưa khóa mã
  const [exporting, setExporting] = useState(false)
  const canQuote = packaging && can(source.entity, 'create')

  //  Ô chọn mã: danh sách mã của CHÍNH màn này (`source.fetchCodes`); nhóm cho chip lấy từ chính danh sách đó.
  useEffect(() => {
    source.fetchCodes().then((d) => { setCodeOptions(sortCodeOptions(d)); setGroups(collectGroups(d)) })
      .catch(() => {}).finally(() => setCodesLoading(false))
  }, [source])

  /** Bộ lọc + thứ tự gửi máy chủ — dùng chung cho danh sách và Xuất Excel. */
  const filterParams = useMemo<PackagingPriceListParams>(() => ({
    code: filters.codes.length ? filters.codes : undefined,
    group: filters.group || undefined,
    //  Đường nguyên liệu không có tham số `scope`.
    ...(packaging ? { scope: filters.scope } : {}),
    date_from: range.from || undefined,
    date_to: range.to || undefined,
    ...(sortBy ? { sort_by: sortBy, sort_dir: sortDir } : {}),
  }), [packaging, filters.codes, filters.group, filters.scope, range, sortBy, sortDir])
  const params = useMemo(() => ({ ...filterParams, page, page_size: pageSize }), [filterParams, page, pageSize])
  const list = useLatestQuery(() => source.fetchList(params), JSON.stringify(params))

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
    //  Mã VTBB bấm sang Lịch sử mua hàng của cụm; mã nguyên liệu là chữ thường (Lịch sử mua hàng không thuộc quyền nguyên liệu).
    { key: 'code', label: source.codeLabel, width: 120, sort: 'code', fixed: true, card: 'title', cell: (r) => (packaging ? <CodeLink code={r.code} /> : <b className="pkg-num">{r.code}</b>) },
    { key: 'name', label: source.nameLabel, width: 250, sort: 'name', card: 'subtitle', cell: (r) => (r.name ? <OneLine>{r.name}</OneLine> : <span className="pkg-muted">(chưa có tên)</span>) },
    { key: 'group', label: 'Nhóm', width: 90, sort: 'group', cell: (r) => r.group },
    { key: 'unit', label: 'ĐVT', width: 70, cell: (r) => r.unit },
    { key: 'purchase_count', label: 'Số lần mua', width: 90, align: 'right', sort: 'purchase_count', cell: (r) => r.purchase_count },
    { key: 'last_date', label: 'Mua gần nhất', width: 110, sort: 'last_date', cell: (r) => (r.last_date ? fmtDateStr(r.last_date) : <Dash />) },
    //  Mọi giá của bảng này tính bằng đồng Việt Nam (người chủ chốt 26/11/2026) — cột chỉ để ghi rõ đơn vị tiền, đặt
    //  ngay trước cột giá đầu tiên để luôn thấy cạnh các cột giá (đặt sau ĐVT thì bị cuộn ngang che mất).
    { key: 'currency', label: 'Tiền tệ', width: 80, cell: () => 'VND' },
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
    //  Ba cột dưới chỉ có ở Bảng giá VTBB (nguyên liệu không nằm trong định mức bao bì, không có luồng Báo giá ở màn này).
    ...(packaging ? [
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
    ] satisfies TableColumn<PackagingPriceRow>[] : []),
  ], [canQuote, packaging, source.codeLabel, source.nameLabel])
  const table = useTableColumns(source.tableKey, columns)
  const minW = table.columns.reduce((s, c) => s + (typeof c.width === 'number' ? c.width : 100), 0)
  const rows = list.data?.items ?? []
  const narrow = useNarrowScreen()
  const emptyText = list.failed ? 'Không tải được bảng giá — thử tải lại.' : list.loading ? 'Đang tải…'
    : filtersActive ? 'Không có mã nào khớp bộ lọc.' : source.emptyText

  async function exportExcel() {
    if (exporting) return
    setExporting(true)
    try { await downloadExport(source.exportPath, filterParams, source.exportName) }
    catch (e: any) { toast.error(e?.message || 'Không xuất được tệp Excel') }
    finally { setExporting(false) }
  }

  return (
    <div>
      <div className="pkg-head" style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 260 }}>
          <h2 className="page-title" style={{ margin: 0 }}>{source.title}</h2>
          <div className="pkg-hint">{source.hint}</div>
        </div>
        <div style={{ width: 280 }}>
          <DateRangePicker block value={range} placeholder="Khoảng ngày tính min – max"
            onChange={(v) => { setRange(v); setPage(1) }} />
        </div>
        {canQuote && <button className="btn" title="Báo giá mới" aria-label="Báo giá mới" onClick={() => setQuoteCode('')}><i className="ti ti-plus" /><span className="pkg-btn-label">Báo giá mới</span></button>}
        {packaging && (
          <PackagingExcelImportButton module={IMPORT_MODULE_PACKAGING_QUOTE} action="create"
            label="Nhập báo giá" title="Nhập báo giá VTBB từ Excel"
            description="Mỗi dòng một báo giá: Mã VTBB, Đơn giá (VNĐ chưa VAT), Ngày hiệu lực; tùy chọn Mã NCC, VAT (%), Ghi chú. Trùng mã + NCC + ngày hiệu lực thì cập nhật, chưa có thì thêm. Chạy thử trước, xem nhật ký rồi bấm Ghi thật." />
        )}
        {can(source.entity, 'export') && (
          <button className="btn outline" disabled={exporting} onClick={exportExcel} title="Xuất Excel" aria-label="Xuất Excel">
            <i className="ti ti-file-spreadsheet" /><span className="pkg-btn-label">{exporting ? 'Đang xuất…' : 'Xuất Excel'}</span>
          </button>
        )}
      </div>

      <div className="card table-card">
        {/* Thanh lọc nằm CÙNG hàng với nút Tải lại / Cột của bảng (người chủ báo dải trống giữa hai hàng, 23/11/2026). */}
        <TableToolbar compact {...table} onRefresh={list.reload}>
          <div className="pkg-row" style={{ flex: 1, minWidth: 0 }}>
            <div style={{ width: 380, maxWidth: '100%' }}>
              <PackagingCodePicker options={codeOptions} value={filters.codes} onChange={(codes) => patch({ codes })}
                loading={codesLoading} kind={source.pickerKind} emptyPlaceholder={source.pickerPlaceholder} compact />
            </div>
            <div className="pkg-pills" role="group" aria-label="Lọc theo nhóm">
              {['', ...groups].map((g) => (
                <button key={g || 'all'} type="button" className={'pkg-pill' + (filters.group === g ? ' on' : '')}
                  aria-pressed={filters.group === g} onClick={() => patch({ group: g })}>{g || 'Tất cả'}</button>
              ))}
            </div>
            {packaging && (
              <div className="pkg-seg" role="group" aria-label="Phạm vi mã">
                <button className={filters.scope === 'bom' ? 'on' : ''} onClick={() => patch({ scope: 'bom' })}>Mã trong định mức</button>
                <button className={filters.scope === 'all' ? 'on' : ''} onClick={() => patch({ scope: 'all' })}>Mọi mã có giá</button>
              </div>
            )}
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
