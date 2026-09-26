// bao-CR-470 — Tra cứu giá hải quan (bản cũ). Thiết kế: doc/erp/hai-quan/04-giao-dien.md.
//
// MỘT màn hình, năm thẻ: Danh sách · Biểu đồ · Nhà nhập khẩu · So sánh · Pháp lý & thuế.
// Đại ca chốt 23/09/2026: biểu đồ nằm chung màn với danh sách, CHỈ hiện khi đã có bộ lọc
// (từ khóa hoặc mã HS); không có trang tổng quan riêng, không tính sẵn, không tác vụ định kỳ.
// Quyền: `customs_price` (đọc / ghi = nạp tệp / xóa = hoàn tác / xuất = Excel).
// bao-CR-493 (yêu cầu phòng Thu mua 25/09, bê từ bản v2): thẻ thứ sáu «Lịch sử nạp» thay hộp thoại;
// hàng «Lọc thêm» sáu ô; doanh nghiệp chọn NHIỀU (chip cộng dồn); hai cột VND ở cuối bảng.
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import FilterPanel, { FilterItem } from '../components/FilterPanel'
import Pagination from '../components/Pagination'
import SearchSelect from '../components/SearchSelect'
import TableHead, { TableCells } from '../components/TableHead'
import TableScroll from '../components/TableScroll'
import TableToolbar from '../components/TableToolbar'
import { toast } from '../components/toast'
import CustomsChart from '../components/customs/CustomsChart'
import CustomsHistoryPanel from '../components/customs/CustomsHistoryPanel'
import CustomsImportDialog from '../components/customs/CustomsImportDialog'
import CustomsLineDetail from '../components/customs/CustomsLineDetail'
import { CustomsCompare, CustomsImporters, CustomsLegal } from '../components/customs/CustomsTabs'
import {
  addNamedId, blobErrorMessage, CustomsFilters, downloadBlob, EMPTY_FILTERS, EXTRA_FILTER_KEYS, fmtDate, fmtQty,
  fmtUsd, fmtVnd, hasChartFilter, NEED_FILTER_MSG, removeNamedId, splitNamedIds, toParams,
} from '../components/customs/customs-shared'
import { TableColumn, useTableColumns } from '../hooks/useTableColumns'
import { formatBannedLabel, formatThresholdKg, sortRegulationsBySeverity } from '../utils/customs-regulation'

const TABS = [
  { key: 'list', label: 'Danh sách', icon: 'ti-list' },
  { key: 'chart', label: 'Biểu đồ', icon: 'ti-chart-line', needFilter: true },
  { key: 'importers', label: 'Nhà nhập khẩu', icon: 'ti-building-factory-2', needFilter: true },
  { key: 'compare', label: 'So sánh', icon: 'ti-arrows-diff' },
  { key: 'legal', label: 'Pháp lý & thuế', icon: 'ti-scale' },
  { key: 'history', label: 'Lịch sử nạp', icon: 'ti-history' },
]

const pct = (v: any) => (v == null || v === '' ? '' : `${v}%`)

// 32 cột ĐÚNG thứ tự và tiêu đề của tệp GTT02, hiện HẾT mặc định (đại ca chốt 23/09/2026),
// rồi hai cột suy ra ở cuối. Ai muốn gọn thì tự ẩn ở menu «Cột».
const COLS: TableColumn[] = [
  { key: 'reg_date', label: 'Ngày đăng ký', width: 105, cell: (r) => (
    <span title={r.date_fixed ? 'Ngày trong tệp bị đảo ngày/tháng — đã đọc lại' : undefined}>
      {fmtDate(r.reg_date)}{r.date_fixed && <i className="ti ti-calendar-repeat" style={{ color: '#d97706', marginLeft: 4 }} />}
    </span>) },
  { key: 'office_code', label: 'Tên nơi mở tờ khai', width: 110 },
  { key: 'importer_tax_code', label: 'Mã doanh nghiệp XNK', width: 120 },
  { key: 'importer_name', label: 'Tên doanh nghiệp XNK', width: 240 },
  { key: 'partner_name', label: 'Đơn vị đối tác', width: 200 },
  { key: 'hs_code', label: 'Mã hàng khai báo', width: 100 },
  { key: 'line_no', label: 'Số thứ tự hàng', width: 80, align: 'right' },
  { key: 'product_name', label: 'Tên hàng', width: 360, td: { whiteSpace: 'normal' } },
  { key: 'price_usd', label: 'Đơn giá khai báo(USD)', width: 125, align: 'right', cell: (r) => fmtUsd(r.price_usd) },
  { key: 'price_nt', label: 'Đơn giá NT khai báo', width: 120, align: 'right', cell: (r) => fmtUsd(r.price_nt) },
  { key: 'adj_price_usd', label: 'Đơn giá điều chỉnh(USD)', width: 130, align: 'right', cell: (r) => fmtUsd(r.adj_price_usd) },
  { key: 'adj_price_nt', label: 'Đơn giá NT điều chỉnh', width: 125, align: 'right', cell: (r) => fmtUsd(r.adj_price_nt) },
  { key: 'currency', label: 'Nguyên tệ', width: 80 },
  { key: 'fx_rate', label: 'Tỷ giá nguyên tệ', width: 110, align: 'right', cell: (r) => fmtUsd(r.fx_rate) },
  { key: 'usd_rate', label: 'Tỷ giá USD', width: 100, align: 'right', cell: (r) => fmtUsd(r.usd_rate) },
  { key: 'quantity', label: 'Lượng', width: 110, align: 'right', cell: (r) => fmtQty(r.quantity) },
  { key: 'unit_code', label: 'Đơn vị tính', width: 80 },
  { key: 'origin_country', label: 'Tên nước xuất xứ', width: 120 },
  { key: 'contract_no', label: 'Số hợp đồng', width: 130 },
  { key: 'contract_date', label: 'Ngày hợp đồng', width: 105, cell: (r) => fmtDate(r.contract_date) },
  { key: 'incoterm', label: 'Điều kiện giao hàng', width: 90 },
  { key: 'transport_mode', label: 'Phương tiện vận chuyển', width: 130, cell: (r) => r.transport_label || r.transport_mode || '' },
  { key: 'rate_import', label: 'Thuế suất XNK', width: 90, align: 'right', cell: (r) => pct(r.rate_import) },
  { key: 'rate_excise', label: 'Thuế suất TTĐB', width: 90, align: 'right', cell: (r) => pct(r.rate_excise) },
  { key: 'rate_vat', label: 'Thuế suất VAT', width: 90, align: 'right', cell: (r) => pct(r.rate_vat) },
  { key: 'rate_safeguard', label: 'Thuế suất tự vệ', width: 90, align: 'right', cell: (r) => pct(r.rate_safeguard) },
  { key: 'tax_import', label: 'Thuế XNK', width: 115, align: 'right', cell: (r) => fmtUsd(r.tax_import) },
  { key: 'tax_excise', label: 'Thuế TTĐB', width: 110, align: 'right', cell: (r) => fmtUsd(r.tax_excise) },
  { key: 'tax_vat', label: 'Thuế VAT', width: 110, align: 'right', cell: (r) => fmtUsd(r.tax_vat) },
  { key: 'tax_environment', label: 'Thuế môi trường', width: 115, align: 'right', cell: (r) => fmtUsd(r.tax_environment) },
  { key: 'tax_safeguard', label: 'Thuế tự vệ', width: 110, align: 'right', cell: (r) => fmtUsd(r.tax_safeguard) },
  { key: 'import_country', label: 'Nước nhập khẩu', width: 110 },
  { key: 'active_ingredient', label: 'Hoạt chất (suy ra)', width: 160 },
  { key: 'formulation', label: 'Hàm lượng / dạng (suy ra)', width: 130 },
  // bao-CR-493 — hai cột VND (giá hiệu lực × tỷ giá USD × thuế), cùng thứ tự với Excel xuất ra.
  { key: 'price_vnd_flat', label: 'Giá VND (thuế NK 7%)', width: 130, align: 'right', cell: (r) => fmtVnd(r.price_vnd_flat) },
  { key: 'price_vnd_line_tax', label: 'Giá VND (thuế suất dòng)', width: 130, align: 'right', cell: (r) => fmtVnd(r.price_vnd_line_tax) },
]

export default function CustomsPrices() {
  const { can } = useAuth()
  const [draft, setDraft] = useState<CustomsFilters>({ ...EMPTY_FILTERS })   // ô đang gõ
  const [filters, setFilters] = useState<CustomsFilters>({ ...EMPTY_FILTERS }) // bộ lọc đã áp
  const [tab, setTab] = useState('list')
  const [coverage, setCoverage] = useState<any>(null)
  const [options, setOptions] = useState<any>(null)
  const [alerts, setAlerts] = useState<any[]>([])
  const [rows, setRows] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [loading, setLoading] = useState(false)
  const [detailId, setDetailId] = useState<number | null>(null)
  const [importOpen, setImportOpen] = useState(false)
  const [extraOpen, setExtraOpen] = useState(false)
  const [exporting, setExporting] = useState(false)
  const table = useTableColumns('customs-lines-full', COLS)

  const loadMeta = useCallback(() => {
    api.get('/api/customs/coverage').then((r) => setCoverage(r.data.data))
    api.get('/api/customs/options').then((r) => setOptions(r.data.data))
  }, [])
  useEffect(() => { loadMeta() }, [loadMeta])

  const loadLines = useCallback(() => {
    setLoading(true)
    api.get('/api/customs/lines', { params: { ...toParams(filters), page, page_size: pageSize } })
      .then((r) => { setRows(r.data.data.items); setTotal(r.data.data.total) })
      .finally(() => setLoading(false))
  }, [filters, page, pageSize])
  useEffect(() => { if (tab === 'list') loadLines() }, [tab, loadLines])

  useEffect(() => {
    if ((filters.q || '').trim().length < 3) { setAlerts([]); return }
    api.get('/api/customs/alerts', { params: toParams(filters) }).then((r) => setAlerts(r.data.data)).catch(() => setAlerts([]))
  }, [filters])

  function apply(next: CustomsFilters = draft) {
    setPage(1)
    setFilters({ ...next })
  }
  function clearAll() {
    setDraft({ ...EMPTY_FILTERS })
    apply({ ...EMPTY_FILTERS })
  }
  // bao-CR-493: chọn thêm từ thẻ Nhà nhập khẩu là CỘNG DỒN vào bộ lọc, không thay thế.
  function pickImporter(id: number, name: string) {
    const merged = addNamedId(filters.importer_id, filters.importer_name, id, name)
    const next = { ...draft, importer_id: merged.ids, importer_name: merged.names }
    setDraft(next)
    apply(next)
    setTab('list')
  }
  function dropImporter(id: string) {
    const merged = removeNamedId(filters.importer_id, filters.importer_name, id)
    const next = { ...draft, importer_id: merged.ids, importer_name: merged.names }
    setDraft(next)
    apply(next)
  }
  function pickPartner(id: number, name: string) {
    const merged = addNamedId(filters.partner_id, filters.partner_name, id, name)
    const next = { ...draft, partner_id: merged.ids, partner_name: merged.names }
    setDraft(next)
    apply(next)
    setDetailId(null)
    setTab('list')
  }
  function dropPartner(id: string) {
    const merged = removeNamedId(filters.partner_id, filters.partner_name, id)
    const next = { ...draft, partner_id: merged.ids, partner_name: merged.names }
    setDraft(next)
    apply(next)
  }
  function refreshAll() {
    loadMeta()
    loadLines()
  }

  async function exportXlsx() {
    if (exporting) return
    setExporting(true)
    try {
      await downloadBlob(api, '/api/customs/lines/export', 'tra-cuu-gia-hai-quan.xlsx', toParams(filters))
    } catch (e: any) {
      toast.error(await blobErrorMessage(e, 'Không xuất được tệp Excel'))
    } finally {
      setExporting(false)
    }
  }

  const set = (k: keyof CustomsFilters) => (v: string) => setDraft((s) => ({ ...s, [k]: v }))
  const optionList = (key: string) => (options?.[key] || []).map((o: any) => ({ value: o.value, label: `${o.label ?? o.value} (${o.count})` }))
  const importerChips = useMemo(() => splitNamedIds(filters.importer_id, filters.importer_name), [filters.importer_id, filters.importer_name])
  const partnerChips = useMemo(() => splitNamedIds(filters.partner_id, filters.partner_name), [filters.partner_id, filters.partner_name])
  const extraActive = EXTRA_FILTER_KEYS.some((k) => draft[k] || filters[k])
  const dirty = useMemo(() => Object.values(filters).some((v) => v), [filters])
  // Gõ thẳng đường dẫn mà thiếu quyền: nói đúng lý do, đừng để bảng rỗng trông như "không khớp bộ lọc".
  // (Chặn thật nằm ở backend — mọi đường /api/customs đều require('customs_price', ...).)
  if (!can('customs_price', 'read')) return (
    <div className="card" style={{ padding: 24, color: 'var(--muted)' }}>
      Tài khoản chưa được cấp quyền <b>Tra cứu giá hải quan</b>. Nhờ quản trị tick quyền này trên vai trò của bạn.
    </div>
  )

  const chartReady = hasChartFilter(filters)
  // Khóa theo bộ lọc: đổi lọc là dựng lại thẻ biểu đồ / xếp hạng với đơn vị mặc định — một lượt gọi API thay vì hai.
  const filterKey = JSON.stringify(toParams(filters))
  const empty = coverage && coverage.total === 0

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <h2 className="page-title" style={{ margin: 0, flex: 1 }}>Tra cứu giá hải quan</h2>
        {can('customs_regulation', 'read') && (
          <Link className="btn ghost" to="/customs-regulations"><i className="ti ti-book" />Danh mục hóa chất</Link>
        )}
        <button className="btn ghost" onClick={() => setTab('history')}><i className="ti ti-history" />Lịch sử nạp</button>
        {can('customs_price', 'write') && (
          <button className="btn" onClick={() => setImportOpen(true)}><i className="ti ti-upload" />Nạp dữ liệu</button>
        )}
      </div>

      <CoverageStrip coverage={coverage} ingredient={options?.ingredient_coverage} />

      <FilterPanel canClear={dirty || Object.values(draft).some((v) => v)} onClear={clearAll}
        extra={<button className="btn" onClick={() => apply()}><i className="ti ti-search" />Tìm</button>}>
        <FilterItem label="Tên hàng / hoạt chất" grow>
          <input value={draft.q} onChange={(e) => set('q')(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && apply()}
            placeholder="vd ATRAZINE, mancozeb, glyphosate…" />
        </FilterItem>
        <FilterItem label="Mã HS" width={150}>
          <SearchSelect value={draft.hs_code} placeholder="Tất cả" autoSelectSingle={false}
            options={optionList('hs_codes')} onChange={set('hs_code')} />
        </FilterItem>
        <FilterItem label="Xuất xứ" width={150}>
          <SearchSelect value={draft.origin} placeholder="Tất cả" autoSelectSingle={false}
            options={optionList('origins')} onChange={set('origin')} />
        </FilterItem>
        <FilterItem label="Đơn vị tính" width={120}>
          <SearchSelect value={draft.unit} placeholder="Tất cả" autoSelectSingle={false}
            options={optionList('units')} onChange={set('unit')} />
        </FilterItem>
        <FilterItem label="Hàm lượng / dạng" width={150}>
          <SearchSelect value={draft.formulation} placeholder="Tất cả" autoSelectSingle={false}
            options={optionList('formulations')} onChange={set('formulation')} />
        </FilterItem>
        <FilterItem label="Từ tháng" width={140}>
          <input type="month" value={draft.date_from} onChange={(e) => set('date_from')(e.target.value)} />
        </FilterItem>
        <FilterItem label="Đến tháng" width={140}>
          <input type="month" value={draft.date_to} onChange={(e) => set('date_to')(e.target.value)} />
        </FilterItem>
        <FilterItem label=" " width={110}>
          <button className="btn ghost" type="button" onClick={() => setExtraOpen((o) => !o)}>
            <i className={`ti ${extraOpen || extraActive ? 'ti-chevron-up' : 'ti-chevron-down'}`} />Lọc thêm
          </button>
        </FilterItem>
        {(extraOpen || extraActive) && (
          /* bao-CR-493 — sáu ô theo sheet 4 yêu cầu phòng Thu mua. Khoảng số nhập chữ, backend bỏ ô rác;
             giá so trên GIÁ HIỆU LỰC (điều chỉnh nếu có). */
          <>
            <FilterItem label="Nguyên tệ" width={110}>
              <SearchSelect value={draft.currency} placeholder="Tất cả" autoSelectSingle={false}
                options={optionList('currencies')} onChange={set('currency')} />
            </FilterItem>
            <FilterItem label="Điều kiện giao hàng" width={130}>
              <SearchSelect value={draft.incoterm} placeholder="Tất cả" autoSelectSingle={false}
                options={optionList('incoterms')} onChange={set('incoterm')} />
            </FilterItem>
            <FilterItem label="Tệp nguồn (lô nạp)" width={200}>
              <SearchSelect value={draft.batch_id} placeholder="Tất cả" autoSelectSingle={false}
                options={optionList('batches')} onChange={set('batch_id')} />
            </FilterItem>
            <FilterItem label="Đơn giá USD từ – tới" width={190}>
              <div style={{ display: 'flex', gap: 4 }}>
                <input inputMode="decimal" placeholder="từ" value={draft.price_min} onChange={(e) => set('price_min')(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && apply()} />
                <input inputMode="decimal" placeholder="tới" value={draft.price_max} onChange={(e) => set('price_max')(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && apply()} />
              </div>
            </FilterItem>
            <FilterItem label="Lượng từ – tới" width={190}>
              <div style={{ display: 'flex', gap: 4 }}>
                <input inputMode="decimal" placeholder="từ" value={draft.qty_min} onChange={(e) => set('qty_min')(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && apply()} />
                <input inputMode="decimal" placeholder="tới" value={draft.qty_max} onChange={(e) => set('qty_max')(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && apply()} />
              </div>
            </FilterItem>
            <FilterItem label="Tỷ giá USD từ – tới" width={190}>
              <div style={{ display: 'flex', gap: 4 }}>
                <input inputMode="decimal" placeholder="từ" value={draft.rate_min} onChange={(e) => set('rate_min')(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && apply()} />
                <input inputMode="decimal" placeholder="tới" value={draft.rate_max} onChange={(e) => set('rate_max')(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && apply()} />
              </div>
            </FilterItem>
          </>
        )}
      </FilterPanel>

      {(importerChips.length > 0 || partnerChips.length > 0) && (
        <div style={{ marginBottom: 8, fontSize: 13, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {importerChips.map((chip) => (
            <span key={`i-${chip.id}`} className="badge info" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              Doanh nghiệp: {chip.name || `#${chip.id}`}
              <i className="ti ti-x" style={{ cursor: 'pointer' }} title={`Bỏ lọc doanh nghiệp ${chip.name || chip.id}`}
                onClick={() => dropImporter(chip.id)} />
            </span>
          ))}
          {partnerChips.map((chip) => (
            <span key={`p-${chip.id}`} className="badge info" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              Đối tác: {chip.name || `#${chip.id}`}
              <i className="ti ti-x" style={{ cursor: 'pointer' }} title={`Bỏ lọc đối tác ${chip.name || chip.id}`}
                onClick={() => dropPartner(chip.id)} />
            </span>
          ))}
        </div>
      )}

      {alerts.length > 0 && (
        <div style={{ border: '1px solid #fecaca', background: '#fef2f2', color: '#991b1b', borderRadius: 8,
          padding: '8px 12px', fontSize: 13, marginBottom: 10 }}>
          <i className="ti ti-alert-triangle" /> <b>Lưu ý pháp lý cho «{filters.q}»:</b>
          <ul style={{ margin: '4px 0 0', paddingLeft: 20 }}>
            {/* bao-CR-477 (bản cũ): dải chỉ bày 5 mục nên xếp nặng nhất lên đầu, và bôi đậm con số */}
            {sortRegulationsBySeverity(alerts).slice(0, 5).map((a) => (
              <li key={a.id}>
                {a.name}{a.cas_no ? ` (CAS ${a.cas_no})` : ''} —{' '}
                {a.list_code === 10 && <b>{formatBannedLabel(a.banned_year)}. </b>}
                {a.list_code !== 10 && formatThresholdKg(a.threshold_kg) && <b>Ngưỡng {formatThresholdKg(a.threshold_kg)}. </b>}
                {a.obligation}
              </li>
            ))}
          </ul>
          {alerts.length > 5 && <div style={{ marginTop: 4 }}>… và {alerts.length - 5} mục khác — xem thẻ Pháp lý & thuế.</div>}
        </div>
      )}

      <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid #e5e7eb', marginBottom: 12 }}>
        {TABS.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            style={{ background: 'none', border: 'none', padding: '8px 14px', cursor: 'pointer', fontSize: 14,
              borderBottom: tab === t.key ? '2px solid var(--teal)' : '2px solid transparent',
              color: tab === t.key ? 'var(--teal)' : 'var(--muted)', fontWeight: tab === t.key ? 600 : 400 }}>
            <i className={`ti ${t.icon}`} style={{ marginRight: 5 }} />{t.label}
          </button>
        ))}
      </div>

      {tab === 'list' && (
        <div className="card table-card">
          <TableToolbar {...table} onRefresh={loadLines}>
            {can('customs_price', 'export') && (
              <button className="btn ghost" disabled={exporting || !total} onClick={exportXlsx}
                title="Xuất đúng các dòng đang lọc (tối đa 50.000 dòng)">
                <i className="ti ti-file-spreadsheet" />{exporting ? 'Đang xuất…' : 'Xuất Excel'}
              </button>
            )}
          </TableToolbar>
          <TableScroll>
            <table>
              <TableHead {...table} />
              <tbody>
                {rows.map((r, i) => (
                  <tr key={r.id} className="clickable" onClick={() => setDetailId(r.id)}>
                    <TableCells columns={table.columns} row={r} index={i} />
                  </tr>
                ))}
                {!loading && rows.length === 0 && (
                  <tr><td colSpan={table.columns.length} className="table-empty">
                    {empty
                      ? <>Chưa có dữ liệu hải quan.{can('customs_price', 'write') ? ' Bấm «Nạp dữ liệu» để tải tệp GTT02.' : ''}</>
                      : 'Không có dòng hàng nào khớp bộ lọc — thử bỏ bớt điều kiện hoặc đổi từ khóa.'}
                  </td></tr>
                )}
              </tbody>
            </table>
          </TableScroll>
          <div className="table-foot">
            <Pagination page={page} pageSize={pageSize} total={total} onChange={(p, s) => { setPage(p); setPageSize(s) }} />
          </div>
        </div>
      )}

      {(tab === 'chart' || tab === 'importers') && !chartReady && (
        <div className="card" style={{ padding: 24, textAlign: 'center', color: 'var(--muted)' }}>
          <i className="ti ti-filter" style={{ fontSize: 28, display: 'block', marginBottom: 6 }} />
          {NEED_FILTER_MSG}
          <div style={{ fontSize: 12, marginTop: 6 }}>
            Biểu đồ của toàn bộ dữ liệu là trộn hàng nghìn mặt hàng, kg lẫn lít — con số không có nghĩa.
          </div>
        </div>
      )}
      {tab === 'chart' && chartReady && <CustomsChart key={filterKey} filters={filters} />}
      {tab === 'importers' && chartReady && <CustomsImporters key={filterKey} filters={filters} onPickImporter={pickImporter} />}
      {tab === 'compare' && <CustomsCompare filters={filters} />}
      {tab === 'legal' && <CustomsLegal filters={filters} alerts={alerts} />}
      {tab === 'history' && <CustomsHistoryPanel onChanged={refreshAll} />}

      {detailId != null && (
        <CustomsLineDetail id={detailId} onClose={() => setDetailId(null)}
          onFilterImporter={(id, name) => { pickImporter(id, name); setDetailId(null) }} onFilterPartner={pickPartner} />
      )}
      {importOpen && <CustomsImportDialog onClose={() => setImportOpen(false)} onApplied={refreshAll} />}
    </div>
  )
}

const MONTHS = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11', 'T12']

// Dải tháng đã phủ — để người xem thấy ngay tháng nào CHƯA nạp (quên một tệp là biểu đồ
// thủng một tháng mà không ai biết). Ba trạng thái: có dữ liệu · trống · chưa tới.
function CoverageStrip({ coverage, ingredient }: { coverage: any; ingredient?: any }) {
  if (!coverage) return null
  if (!coverage.total) return (
    <div className="card" style={{ padding: '10px 14px', marginBottom: 10, fontSize: 13, color: 'var(--muted)' }}>
      Chưa có dữ liệu hải quan nào.
    </div>
  )
  const now = new Date()
  const future = (y: number, m: number) => y > now.getFullYear() || (y === now.getFullYear() && m > now.getMonth())
  return (
    <div className="card" style={{ padding: '10px 14px', marginBottom: 10, fontSize: 13 }}>
      <div style={{ marginBottom: 6 }}>
        Dữ liệu: <b>{fmtDate(coverage.date_from)} → {fmtDate(coverage.date_to)}</b> · {fmtQty(coverage.total)} dòng hàng
        {coverage.last_import_at && <> · lần nạp gần nhất {fmtDate(coverage.last_import_at)}</>}
        {ingredient?.ratio != null && (
          <span title="Tỷ lệ dòng hàng nhận ra được hoạt chất từ tên hàng — dòng không nhận ra vẫn tìm được bằng tên hàng">
            {' '}· nhận ra hoạt chất {(ingredient.ratio * 100).toFixed(0)}%
          </span>
        )}
      </div>
      {coverage.years.map((y: any) => (
        <div key={y.year} style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 2 }}>
          <span style={{ width: 40, color: 'var(--muted)' }}>{y.year}</span>
          {y.months.map((n: number, i: number) => {
            const fut = future(y.year, i)
            return (
              <span key={i} title={fut ? `${MONTHS[i]}/${y.year}: chưa tới` : `${MONTHS[i]}/${y.year}: ${n} dòng`}
                style={{ width: 44, textAlign: 'center', fontSize: 11, borderRadius: 4, padding: '2px 0',
                  background: fut ? '#f8fafc' : n ? '#dcf2fb' : '#fee2e2',
                  color: fut ? '#cbd5e1' : n ? '#0369a1' : '#b91c1c',
                  border: fut ? '1px dashed #e2e8f0' : '1px solid transparent' }}>
                {MONTHS[i]}
              </span>
            )
          })}
        </div>
      ))}
    </div>
  )
}
