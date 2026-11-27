import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import { toast } from '../../components/toast'
import PackagingExcelImportButton from '../../components/packaging/PackagingExcelImportButton'
import PackagingHistoryChart from '../../components/packaging/PackagingHistoryChart'
import PackagingHistoryMultiChart from '../../components/packaging/PackagingHistoryMultiChart'
import { normalizeSeriesByCode } from '../../utils/packaging-multi-series-chart'
import PackagingHistoryTable from '../../components/packaging/PackagingHistoryTable'
import PackagingHistoryToolbar from '../../components/packaging/PackagingHistoryToolbar'
import type { PackagingPickerKind } from '../../components/packaging/PackagingCodePicker'
import {
  IMPORT_MODULE_PACKAGING_MISA, PACKAGING_ENTITY, downloadExport, fetchCodeOptions, fetchFgOptions, fetchHistory,
  type PackagingEntity, type PackagingExportPath,
} from '../../api/packaging-cost'
import type { PackagingCodeOption, PackagingHistoryParams, PackagingHistoryResult } from '../../api/packaging-cost-types'
import { useDebouncedValue } from '../../hooks/use-debounced-value'
import { useLatestQuery } from '../../hooks/use-latest-query'
import { buildHistorySummary } from '../../utils/packaging-history-summary'
import { historyPrintHref } from '../../utils/packaging-print'
import {
  buildHistoryParams, buildHistorySearch, EMPTY_HISTORY_FILTERS, nextSort,
  parseHistorySearch, sortCodeOptions, type HistoryFilters, type HistorySelection,
} from '../../utils/packaging-query'
import '../../components/packaging/packaging.css'

/**
 * bao-CR-801 — NGUỒN DỮ LIỆU + chữ của một màn lịch sử mua hàng. Hai màn Lịch sử mua hàng (VTBB) và Lịch sử mua nguyên
 * liệu dùng CHUNG khung (`PackagingHistoryScreen`), chỉ khác bộ này: mỗi màn gọi đường riêng và hỏi khóa quyền riêng của
 * mình, không gọi chéo. `P` = kiểu tham số máy chủ của màn (đường nguyên liệu không có `mode` / `fg_codes`).
 */
export interface HistorySource<P extends object> {
  /** Khóa quyền của màn: `export` cho nút Xuất Excel, `read` cho nút In (khi có `printHref`). */
  entity: PackagingEntity
  /**
   * Phần CHỈ CÓ ở màn VTBB: chế độ "Theo mã sản phẩm" (hai nút chế độ + ô chọn sản phẩm + biểu đồ nhiều đường), nút Nạp sổ
   * Misa và mã trong bảng bấm sang lịch sử của đúng mã đó. Màn nguyên liệu tắt hết: chỉ chế độ theo mã, mã là chữ thường.
   */
  packaging: boolean
  /** Khóa lưu cấu hình cột của bảng; bỏ trống = khóa của màn VTBB theo chế độ. */
  tableKey?: string
  title: string
  hint: string
  codeLabel: string
  nameLabel: string
  pickerKind: PackagingPickerKind
  pickerPlaceholder: string
  /** Câu báo khi không nạp được danh sách mã cho ô chọn. */
  codesError: string
  exportPath: PackagingExportPath
  exportName: string
  /** Lựa chọn trên URL + bộ lọc + cột xếp → tham số máy chủ (danh sách VÀ Xuất Excel dùng chung). */
  buildParams: (sel: HistorySelection, f: HistoryFilters, search: string, sort: { by: string; dir: 'asc' | 'desc' }) => P
  fetchList: (params: P & { page: number; page_size: number }) => Promise<PackagingHistoryResult>
  fetchCodes: () => Promise<PackagingCodeOption[]>
  /** Đường của trang in theo đúng bộ lọc đang áp; không khai = màn không có nút In. */
  printHref?: (params: P) => string
}

const PACKAGING_SOURCE: HistorySource<PackagingHistoryParams> = {
  entity: PACKAGING_ENTITY.history,
  packaging: true,
  title: 'Lịch sử mua hàng',
  hint: 'Từng lần mua của mã vật tư bao bì hoặc của thành phần trong định mức sản phẩm, mới nhất trước. Giá VNĐ, chưa VAT, là bản chụp lúc mua: đỏ = đắt hơn lần trước, xanh = rẻ hơn.',
  codeLabel: 'Mã VTBB',
  nameLabel: 'Tên vật tư',
  pickerKind: 'material',
  pickerPlaceholder: 'Tất cả mã VTBB — gõ mã, tên, nhóm hoặc NCC để chọn mã cụ thể',
  codesError: 'Không nạp được danh sách mã bao bì',
  exportPath: 'history',
  exportName: 'lich-su-mua-hang.xlsx',
  buildParams: buildHistoryParams,
  fetchList: fetchHistory,
  fetchCodes: () => fetchCodeOptions('all'),
  printHref: historyPrintHref,
}

/**
 * Màn LỊCH SỬ MUA HÀNG: từng lần mua của mã VTBB, hoặc của các thành phần trong định mức của một / nhiều sản phẩm; kèm
 * dòng KPI và biểu đồ "Diễn biến đơn giá" khi chọn đúng một mã. Lịch sử là bản chụp BẤT BIẾN của sổ giá — không có ô sửa
 * đơn giá (sai thì sửa ở ĐMH / nguồn nạp). Lọc + xếp + phân trang tại MÁY CHỦ. Lựa chọn mã nằm ở URL (`?codes=A,B` ·
 * `?fg=HH1,HH2` · `mode`) để các bảng khác dẫn thẳng vào được.
 */
export default function PackagingHistory() {
  return <PackagingHistoryScreen source={PACKAGING_SOURCE} />
}

/** Khung chung của hai màn lịch sử mua hàng (VTBB / nguyên liệu, bao-CR-801) — `source` quyết định đường gọi, khóa quyền và phần riêng của VTBB. */
export function PackagingHistoryScreen<P extends object>({ source }: { source: HistorySource<P> }) {
  const { can } = useAuth()
  const { packaging } = source
  const [searchParams, setSearchParams] = useSearchParams()
  //  Màn nguyên liệu chỉ có chế độ theo mã: `mode` / `fg` lạc trên URL bị bỏ qua (và rơi khỏi URL ở lần đổi lựa chọn kế).
  const selection = useMemo<HistorySelection>(() => {
    const parsed = parseHistorySearch(searchParams)
    return packaging ? parsed : { mode: 'code', codes: parsed.codes, fg: [] }
  }, [searchParams, packaging])
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

  //  Ô chọn mã: danh sách mã của CHÍNH màn này (`source.fetchCodes`).
  useEffect(() => {
    source.fetchCodes().then((d) => setCodeOptions(sortCodeOptions(d)))
      .catch(() => toast.error(source.codesError))
      .finally(() => setCodesLoading(false))
  }, [source])
  //  Danh sách sản phẩm (~1.000) chỉ nạp khi vào chế độ "Theo mã sản phẩm" — màn nguyên liệu không có chế độ này nên
  //  không bao giờ gọi `fg-options` (`isProduct` luôn sai).
  useEffect(() => {
    if (!isProduct || productsLoaded) return
    setProductsLoading(true)
    fetchFgOptions().then((d) => { setProductOptions(d.map((x) => ({ ...x, group: '', usage: 0, new: null }))); setProductsLoaded(true) })
      .catch(() => toast.error('Không nạp được danh sách sản phẩm'))
      .finally(() => setProductsLoading(false))
  }, [isProduct, productsLoaded])

  //  Bấm một mã ngay trên bảng này (hoặc dùng nút Back) đổi URL mà không qua `changeSelection` → cũng về trang 1.
  const urlKey = searchParams.toString()
  useEffect(() => { setPage(1) }, [urlKey])

  /** Bộ lọc + thứ tự gửi máy chủ — dùng chung cho danh sách và Xuất Excel. */
  const filterParams = useMemo(() => source.buildParams(selection, filters, q, { by: sortBy, dir: sortDir }), [source, selection, filters, q, sortBy, sortDir])
  const params = useMemo(() => ({ ...filterParams, page, page_size: pageSize }), [filterParams, page, pageSize])
  const list = useLatestQuery(() => source.fetchList(params), JSON.stringify(params))
  const series = list.data?.series ?? null
  const singleCode = series !== null
  //  Chế độ sản phẩm với đúng một sản phẩm: mỗi mã thành phần một đường giá (máy chủ cũ không trả trường này).
  const seriesByCode = useMemo(() => normalizeSeriesByCode(list.data?.series_by_code), [list.data?.series_by_code])

  //  Đổi lựa chọn mã / bộ lọc / cột xếp → về trang 1 (đặt cùng lúc với setter để khỏi gọi máy chủ hai lần).
  const changeSelection = (next: HistorySelection) => { setSearchParams(buildHistorySearch(next), { replace: true }); setPage(1) }
  const changeFilters = (next: HistoryFilters) => { setFilters(next); setPage(1) }
  const onSort = (key: string) => { const s = nextSort(sortBy, sortDir, key); setSortBy(s.by); setSortDir(s.dir); setPage(1) }
  const filtersActive = JSON.stringify(filters) !== JSON.stringify(EMPTY_HISTORY_FILTERS)

  async function exportExcel() {
    if (exporting) return
    setExporting(true)
    try { await downloadExport(source.exportPath, filterParams, source.exportName) }
    catch (e: any) { toast.error(e?.message || 'Không xuất được tệp Excel') }
    finally { setExporting(false) }
  }

  const stats = list.data?.stats
  //  Thẻ số liệu trình bày y bản mẫu HTML (người chủ chốt 23/11/2026): thẻ trắng, viền trên xanh lá, số to navy, một dòng
  //  phụ xám; bộ thẻ đổi theo cách xem (một mã / nhiều mã / theo sản phẩm), xem `buildHistorySummary`.
  const summaryCards = stats ? (
    <div className="pkg-kpis">
      {buildHistorySummary(stats, {
        singleCode, mode: selection.mode, selectedCount: isProduct ? selection.fg.length : selection.codes.length,
      }).map((it) => (
        <div key={it.label} className="pkg-kpi">
          <div className="pkg-kpi-k">{it.label}</div>
          <div className={['pkg-kpi-v', it.tone, it.value.length > 10 && 'long'].filter(Boolean).join(' ')} title={it.value}>{it.value}</div>
          <div className="pkg-kpi-s" title={it.sub}>{it.sub || '\u00a0'}</div>
        </div>
      ))}
    </div>
  ) : null
  const first = list.data?.items[0]
  const printHref = source.printHref

  return (
    <div>
      <div className="pkg-head" style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 260 }}>
          <h2 className="page-title" style={{ margin: 0 }}>{source.title}</h2>
          <div className="pkg-hint">{source.hint}</div>
        </div>
        {/* In = xem (quyền đọc). Mở tab mới với ĐÚNG bộ lọc đang áp; trang in tự nạp đủ mọi dòng. Màn nguyên liệu không có trang in. */}
        {printHref && can(source.entity, 'read') && (
          <button className="btn outline" aria-label="In" title="In" onClick={() => window.open(printHref(filterParams), '_blank')}>
            <i className="ti ti-printer" /><span className="pkg-btn-label">In</span>
          </button>
        )}
        {packaging && (
          <PackagingExcelImportButton module={IMPORT_MODULE_PACKAGING_MISA} action="write"
            label="Nạp sổ Misa" title="Nạp Sổ chi tiết mua hàng Misa"
            description="Tệp Excel Sổ chi tiết mua hàng xuất từ Misa (cột Ngày, Mã hàng, Số lượng, Đơn giá, Tên NCC, Tên kho…). Chỉ thay dữ liệu Misa trong khoảng ngày của tệp, dòng trùng giữ nguyên, ngoài khoảng không đổi; mốc sổ Misa dời theo ngày lớn nhất. Chạy thử trước, xem nhật ký rồi bấm Ghi thật." />
        )}
        {can(source.entity, 'export') && (
          <button className="btn outline" disabled={exporting} onClick={exportExcel} title="Xuất Excel" aria-label="Xuất Excel">
            <i className="ti ti-file-spreadsheet" /><span className="pkg-btn-label">{exporting ? 'Đang xuất…' : 'Xuất Excel'}</span>
          </button>
        )}
      </div>

      <div className="card pkg-card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <PackagingHistoryToolbar selection={selection} onSelection={changeSelection} filters={filters} onFilters={changeFilters}
          codeOptions={codeOptions} productOptions={productOptions} optionsLoading={isProduct ? productsLoading : codesLoading}
          suppliers={list.data?.suppliers ?? []}
          modeSwitch={packaging} codeKind={source.pickerKind} codePlaceholder={source.pickerPlaceholder} />
        {summaryCards}
        {series && series.length > 0 && (
          <PackagingHistoryChart series={series} subject={[first?.code, first?.name].filter(Boolean).join(' · ')} />
        )}
        {seriesByCode.length > 0 && (
          <PackagingHistoryMultiChart series={seriesByCode}
            subject={[list.data?.items[0]?.fg_code, list.data?.items[0]?.fg_name].filter(Boolean).join(' · ')} />
        )}
        <PackagingHistoryTable rows={list.data?.items ?? []} total={list.data?.total ?? 0} productMode={isProduct} singleCode={singleCode}
          sortBy={sortBy} sortDir={sortDir} onSort={onSort} page={page} pageSize={pageSize}
          onPage={(p, s) => { setPage(p); setPageSize(s) }} onReload={list.reload}
          codeLabel={source.codeLabel} nameLabel={source.nameLabel} plainCode={!packaging} tableKey={source.tableKey}
          empty={list.failed ? 'Không tải được lịch sử — thử tải lại.' : list.loading ? 'Đang tải…'
            : filtersActive ? 'Không có lần mua nào khớp bộ lọc.' : 'Chưa có lần mua nào cho lựa chọn này.'} />
      </div>
    </div>
  )
}
