import { useEffect, useMemo, useRef, useState } from 'react'
import type { CSSProperties, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import SearchSelect from '../components/SearchSelect'
import DateRangePicker from '../components/DateRangePicker'
import FilterPanel, { FilterItem } from '../components/FilterPanel'
import {
  ConditionalFilter, ConditionalFilterButton, RestQueryParams,
} from '../components/conditional-filter'
import { surveyProgressCondFilters } from '../config/conditional-filters'
import Pagination from '../components/Pagination'
import { fmtDate } from '../utils/datetime'
import TableHead, { TableCells, TableColGroup } from '../components/TableHead'
import TableToolbar from '../components/TableToolbar'
import { useTableColumns, TableColumn } from '../hooks/useTableColumns'
import { useUrlFilters } from '../hooks/use-url-filters'
import { fmtVND } from '../utils/money'
import { toast } from '../components/toast'
import TableScroll from '../components/TableScroll'

/**
 * CR-075 — Tiến độ báo giá.
 *
 * Song sinh của màn Tiến độ mua hàng nhưng đọc chuỗi YÊU CẦU BÁO GIÁ: mỗi hàng = MỘT DÒNG
 * yêu cầu (kèm phương án đã chốt), KHÔNG nở theo phương án — thứ cần theo dõi là "dòng này
 * khảo sát tới đâu rồi", không phải "có mấy báo giá".
 *
 * Ba cột giá trị nhất là ba cột tính ở backend: Trễ hạn, Số ngày xử lý, Tiến độ dòng.
 */

const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
const fmtPrice = (n: any) => Number(n || 0).toLocaleString('vi-VN', { maximumFractionDigits: 4 })
const NOWRAP = { whiteSpace: 'nowrap' as const, overflow: 'hidden', textOverflow: 'ellipsis' }
const MUTED = { color: 'var(--muted)' } as const
const R = { textAlign: 'right' as const }

// Tiến độ dòng — nhãn + màu phải khớp `survey_progress/export.py` (STATE_*)
const PG_COLOR: Record<string, string> = {
  'Chưa tiếp nhận': '#94a3b8', 'Đã tiếp nhận': '#64748b', 'Đang khảo sát': '#d97706',
  'Đã trả kết quả': '#00AEEF', 'Chốt rỗng': '#a855f7', 'Đã chọn phương án': '#0d9488',
  'Cần khảo sát lại': '#dc2626', 'Đã tạo YCMH': '#7c3aed', 'Hoàn thành': '#16a34a',
}

/** Bộ lọc rỗng — dùng cho khởi tạo và nút "Xóa lọc".
 *
 *  CR-080: thanh lọc rút về mấy ô CƠ BẢN. Phân loại / NSTM / trạng thái phiếu / trạng thái dòng /
 *  tháng / hạn trả KQ / ngày trả KQ / "đã trả kết quả" đều chuyển sang BỘ LỌC ĐIỀU KIỆN — ở đó
 *  còn lọc được "trước ngày", "trong khoảng", "đang trống" (chưa trả kết quả = Ngày trả KQ đang
 *  trống). Backend VẪN đọc các param cũ cho ai gọi API trực tiếp, chỉ là FE không còn ô nhập.
 *
 *  Giữ `state` (Tiến độ dòng) và `late` (Trễ hạn) vì cả hai là cột TÍNH — bộ lọc điều kiện chỉ
 *  chạy trên cột thật trong DB nên không làm được. `department` + khoảng `received_date` giữ ở
 *  ngoài (CR-081), song song với màn Tiến độ mua hàng: hai lát cắt "phòng nào" và "trong quãng
 *  thời gian nào" dùng gần như mọi lần mở màn. */
const EMPTY_FILTERS = {
  company_id: '', department: '', q: '', state: '', late: '',
  received_date_from: '', received_date_to: '',
}

const pgBadge = (s: string) =>
  <span className="badge" style={{ background: (PG_COLOR[s] || '#94a3b8') + '22', color: PG_COLOR[s] || '#64748b', whiteSpace: 'nowrap' }}>{s || '—'}</span>

/** Trễ hạn: backend chỉ trả số DƯƠNG (hoặc rỗng). Rỗng = đúng hạn/chưa tới hạn -> gạch ngang. */
const lateCell = (n: number | null) =>
  n ? <span style={{ color: 'var(--red)', fontWeight: 600 }}>{n}</span> : <span style={MUTED}>—</span>

const numCell = (n: number | null) => (n === null || n === undefined ? <span style={MUTED}>—</span> : fmt(n))

type Ctx = {
  canOpenSR: boolean
  navigate: (p: string) => void
  page: number
  pageSize: number
}

type Col = {
  key: string
  label: string
  w: number
  sort?: string          // key gửi lên backend (cột thật) — không có => không sort được
  sup?: boolean          // chỉ hiện khi có quyền xem NCC (`supplier.read`)
  hide?: boolean         // cột phụ: mặc định ẩn, bật lại ở menu "Cột"
  td?: CSSProperties
  cell: (r: any, ctx: Ctx, i: number) => ReactNode
}

// Khai báo 1 lần: dùng chung cho <colgroup>, <thead> và <tbody> nên index luôn khớp.
const COLS: Col[] = [
  { key: 'stt', label: 'STT', w: 44, td: { ...R, ...MUTED }, cell: (r, c, i) => r.stt ?? (c.page - 1) * c.pageSize + i + 1 },
  {
    key: 'code', label: 'Mã YCBG', w: 150, sort: 'code', td: NOWRAP,
    cell: (r, c) => c.canOpenSR ? (
      <a href={`/survey-requests/${r.sr_id}`}
        onClick={(e) => { e.preventDefault(); c.navigate(`/survey-requests/${r.sr_id}`) }}
        style={{ cursor: 'pointer', color: 'var(--navy)', fontWeight: 600, textDecoration: 'underline' }}
        title="Mở yêu cầu báo giá">{r.code}</a>
    ) : (
      <span style={{ fontWeight: 600, color: 'var(--navy)' }} title="Bạn không có quyền xem chi tiết yêu cầu báo giá">{r.code}</span>
    ),
  },
  { key: 'company', label: 'Công ty', w: 180, sort: 'company_id', cell: (r) => r.company || '—' },
  { key: 'department', label: 'Bộ phận', w: 140, sort: 'department', cell: (r) => r.department },
  { key: 'requester', label: 'Người yêu cầu', w: 150, sort: 'requester', cell: (r) => r.requester },
  { key: 'purpose', hide: true, label: 'Mục đích', w: 190, sort: 'purpose', cell: (r) => r.purpose },
  { key: 'request_date', hide: true, label: 'Ngày YC', w: 92, sort: 'request_date', td: NOWRAP, cell: (r) => fmtDate(r.request_date) },
  { key: 'status', label: 'TT phiếu', w: 110, sort: 'status', td: NOWRAP, cell: (r) => r.status },
  { key: 'internal_line_code', hide: true, label: 'Mã dòng', w: 120, sort: 'internal_line_code', sup: true, td: { ...NOWRAP, ...MUTED }, cell: (r) => r.internal_line_code },
  { key: 'item_group', label: 'Phân loại', w: 130, sort: 'item_group', cell: (r) => r.item_group },
  { key: 'requirement_detail', label: 'Thông số kỹ thuật', w: 240, td: NOWRAP, cell: (r) => <span title={r.requirement_detail}>{r.requirement_detail}</span> },
  { key: 'other_requirement', hide: true, label: 'Yêu cầu khác', w: 180, td: NOWRAP, cell: (r) => <span title={r.other_requirement}>{r.other_requirement}</span> },
  { key: 'request_qty', label: 'SL dự kiến', w: 90, sort: 'request_qty', td: R, cell: (r) => fmt(r.request_qty) },
  { key: 'uom', label: 'ĐVT', w: 56, sort: 'uom', cell: (r) => r.uom },
  { key: 'proposed_price', hide: true, label: 'Giá đề xuất', w: 110, sort: 'proposed_price', td: R, cell: (r) => fmtPrice(r.proposed_price) },
  { key: 'assignee_name', label: 'NSTM phụ trách', w: 190, sort: 'assignee_name', td: NOWRAP, cell: (r) => r.assignee_name || '—' },
  // ----- Mốc tiến độ: phần cốt lõi của màn này -----
  { key: 'received_date', label: 'Ngày tiếp nhận', w: 108, sort: 'received_date', td: NOWRAP, cell: (r) => fmtDate(r.received_date) },
  { key: 'result_due_date', label: 'Hạn trả KQ', w: 100, sort: 'result_due_date', td: NOWRAP, cell: (r) => fmtDate(r.result_due_date) },
  { key: 'result_date', label: 'Ngày trả KQ', w: 104, sort: 'result_date', td: NOWRAP, cell: (r) => fmtDate(r.result_date) },
  { key: 'days_late', label: 'Trễ (ngày)', w: 84, td: R, cell: (r) => lateCell(r.days_late) },
  { key: 'handling_days', label: 'Số ngày xử lý', w: 96, td: R, cell: (r) => numCell(r.handling_days) },
  { key: 'progress_state', label: 'Tiến độ dòng', w: 150, cell: (r) => pgBadge(r.progress_state) },
  { key: 'line_status', hide: true, label: 'TT dòng', w: 130, sort: 'line_status', cell: (r) => r.line_status || '—' },
  { key: 'option_count', label: 'Số PA', w: 66, td: R, cell: (r) => fmt(r.option_count) },
  // CR-079: BỎ cột "Mã YCMH". Một dòng khảo sát tạo được NHIỀU YCMH (mua lại) và lưu đủ ở
  // tab_survey_request_pr, nhưng cột này đọc `pr_code` trên dòng — ô đó bị ghi đè mỗi lần tạo
  // nên chỉ hiện mã MỚI NHẤT, mã cũ mất hút. Thà không có còn hơn hiện thiếu mà tưởng là đủ.
  // Muốn xem đủ thì mở chi tiết Yêu cầu báo giá, bấm vào phương án -> popup liệt kê hết YCMH.
  // (Ô tìm kiếm vẫn khớp mã YCMH nên gõ mã vẫn tra ra dòng.)
  // ----- Phương án đã chốt -----
  { key: 'opt_label', hide: true, label: 'Phương án chốt', w: 130, cell: (r) => r.opt_label || '—' },
  { key: 'opt_supplier_code', hide: true, label: 'Mã NCC', w: 120, sup: true, td: { ...NOWRAP, ...MUTED }, cell: (r) => r.opt_supplier_code },
  { key: 'opt_supplier_name', label: 'Nhà cung cấp', w: 220, sup: true, cell: (r) => r.opt_supplier_name || '—' },
  { key: 'opt_internal_code', hide: true, label: 'Mã SP theo NCC', w: 140, sup: true, td: { ...NOWRAP, ...MUTED }, cell: (r) => r.opt_internal_code },
  { key: 'opt_product_code', hide: true, label: 'Mã SP hệ thống', w: 140, td: { ...NOWRAP, ...MUTED }, cell: (r) => r.opt_product_code },
  { key: 'opt_product_name', label: 'Tên SP báo giá', w: 220, td: { fontWeight: 500 }, cell: (r) => r.opt_product_name || '—' },
  { key: 'opt_spec', hide: true, label: 'Quy cách', w: 190, td: NOWRAP, cell: (r) => <span title={r.opt_spec}>{r.opt_spec}</span> },
  { key: 'opt_origin', hide: true, label: 'Xuất xứ', w: 110, cell: (r) => r.opt_origin },
  { key: 'opt_quote_unit', hide: true, label: 'ĐVT báo giá', w: 96, cell: (r) => r.opt_quote_unit },
  { key: 'opt_moq', hide: true, label: 'SL tối thiểu', w: 96, td: R, cell: (r) => fmt(r.opt_moq) },
  { key: 'opt_price', label: 'Đơn giá báo', w: 110, td: { ...R, fontWeight: 600 }, cell: (r) => fmtPrice(r.opt_price) },
  { key: 'opt_volume_range', hide: true, label: 'Khoảng SL áp giá', w: 130, cell: (r) => r.opt_volume_range },
  { key: 'opt_vat', hide: true, label: 'VAT%', w: 60, td: R, cell: (r) => r.opt_vat || 0 },
  { key: 'opt_delivery_time', hide: true, label: 'Thời gian giao', w: 130, cell: (r) => r.opt_delivery_time },
  { key: 'opt_delivery_place', hide: true, label: 'Nơi giao', w: 160, td: NOWRAP, cell: (r) => r.opt_delivery_place },
  { key: 'opt_shipping_cost', hide: true, label: 'Phí vận chuyển', w: 116, td: R, cell: (r) => fmtVND(r.opt_shipping_cost) },
  { key: 'opt_sample_ready', hide: true, label: 'Có mẫu', w: 72, cell: (r) => r.opt_sample_ready ? 'Có' : '' },
  { key: 'opt_lab_result', hide: true, label: 'KQ kiểm nghiệm', w: 130, cell: (r) => r.opt_lab_result },
  { key: 'opt_note', hide: true, label: 'Ghi chú NSTM', w: 190, sup: true, td: NOWRAP, cell: (r) => <span title={r.opt_note}>{r.opt_note}</span> },
]

export default function SurveyProgress() {
  const navigate = useNavigate()
  const { can } = useAuth()
  const canOpenSR = can('survey_request', 'read')
  const canExport = can('survey_request', 'export')
  const [rows, setRows] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [showSupplier, setShowSupplier] = useState(true)
  const [states, setStates] = useState<string[]>(Object.keys(PG_COLOR))   // backend là nguồn thật
  const [companies, setCompanies] = useState<any[]>([])
  const [departments, setDepartments] = useState<any[]>([])
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [sortBy, setSortBy] = useState('')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [f, setF] = useUrlFilters<any>({ ...EMPTY_FILTERS })
  // Điều kiện từ BỘ LỌC ĐIỀU KIỆN — thêm ref để queryParams() đọc được giá trị mới nhất
  const [condParams, setCondParams] = useState<RestQueryParams>({})
  const condRef = useRef<RestQueryParams>({})
  condRef.current = condParams
  const condFields = useMemo(() => surveyProgressCondFilters(showSupplier), [showSupplier])
  const setFilter = (k: string, v: any) => { setF((s: any) => ({ ...s, [k]: v })); setPage(1) }

  function handleSort(key: string) {
    const nextDir: 'asc' | 'desc' = (sortBy === key && sortDir === 'asc') ? 'desc' : 'asc'
    setSortBy(key); setSortDir(nextDir); setPage(1)
  }

  /** Tham số gửi lên backend — dùng chung cho danh sách và xuất Excel để hai bên luôn khớp. */
  function queryParams() {
    const p: any = { ...condRef.current }
    Object.entries(f).forEach(([k, v]) => { const val = typeof v === 'string' ? v.trim() : v; if (val) p[k] = val })
    if (sortBy) { p.sort_by = sortBy; p.sort_dir = sortDir }
    return p
  }

  async function load() {
    const r = await api.get('/api/survey-progress', { params: { ...queryParams(), page, page_size: pageSize } })
    const d = r.data.data
    setRows(d.items); setTotal(d.total); setShowSupplier(d.show_supplier)
    if (d.states?.length) setStates(d.states)
  }

  useEffect(() => {
    api.get('/api/companies', { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items)).catch(() => {})
    api.get('/api/departments', { params: { page_size: 500 } })
      .then((r) => setDepartments(r.data.data.items)).catch(() => {})
  }, [])

  // Tự tìm khi đổi filter (debounce) / đổi trang / đổi sort
  const timer = useRef<any>(null)
  useEffect(() => {
    clearTimeout(timer.current)
    timer.current = setTimeout(load, 300)
    return () => clearTimeout(timer.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [f, condParams, page, pageSize, sortBy, sortDir])

  // Đổi điều kiện lọc thì về trang 1, kẻo đang ở trang 5 mà kết quả mới chỉ có 2 trang -> bảng rỗng
  useEffect(() => { setPage(1) }, [condParams])

  const tableColumns = useMemo<TableColumn<any>[]>(() => {
    const ctx: Ctx = { canOpenSR, navigate, page, pageSize }
    return COLS.filter((c) => !c.sup || showSupplier).map((c) => ({
      key: c.key,
      label: c.label,
      sort: c.sort,
      width: c.w,
      align: c.td?.textAlign === 'right' ? 'right' : 'left',
      defaultHidden: c.hide,
      td: c.td,
      cell: (r: any, i: number) => c.cell(r, ctx, i),
    }))
  }, [showSupplier, canOpenSR, page, pageSize])

  const table = useTableColumns('survey-progress', tableColumns)
  const minW = table.columns.reduce((s, c) => s + (typeof c.width === 'number' ? c.width : 100), 0)

  /** Xuất Excel đúng bộ lọc + đúng cột đang hiện (backend chặn ở 5.000 dòng). */
  async function exportXlsx() {
    try {
      const p = queryParams()
      p.cols = table.columns.map((c) => c.key).join(',')
      const r = await api.get('/api/survey-progress/export/xlsx', { params: p, responseType: 'blob' })
      const cd = String(r.headers['content-disposition'] || '')
      const name = /filename="?([^"]+)"?/.exec(cd)?.[1] || 'tien-do-bao-gia.xlsx'
      const url = window.URL.createObjectURL(new Blob([r.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', name)
      document.body.appendChild(link)
      link.click()
      link.parentNode?.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (e: any) {
      // Lỗi trả về cũng ở dạng blob (do responseType) -> đọc text rồi lấy message
      let msg = 'Lỗi khi xuất file Excel'
      try {
        const body = e?.response?.data
        const text = body instanceof Blob ? await body.text() : ''
        msg = JSON.parse(text)?.error?.message || msg
      } catch { /* giữ thông báo mặc định */ }
      toast.error(msg)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
        <h2 className="page-title" style={{ margin: 0 }}>Tiến độ báo giá</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ fontSize: 12.5, color: 'var(--muted)' }}>Theo từng dòng yêu cầu · {fmt(total)} dòng</div>
          {canExport && (
            <button className="btn outline" onClick={exportXlsx} title="Xuất toàn bộ kết quả đang lọc ra Excel">
              <i className="ti ti-file-spreadsheet" />Xuất Excel
            </button>
          )}
        </div>
      </div>

      <ConditionalFilter fields={condFields} onChange={setCondParams}>
      <FilterPanel onClear={() => setF({ ...EMPTY_FILTERS })} canClear={Object.values(f).some((v) => v)}
                   extra={<ConditionalFilterButton />}>
        <FilterItem label="Công ty">
          <SearchSelect value={f.company_id} placeholder="Tất cả"
            options={companies.map((c) => ({ value: String(c.id), label: c.name }))}
            onChange={(v) => setFilter('company_id', v)} />
        </FilterItem>
        <FilterItem label="Bộ phận">
          <SearchSelect value={f.department} placeholder="Tất cả"
            options={departments.map((d) => ({ value: d.name, label: d.name }))}
            onChange={(v) => setFilter('department', v)} />
        </FilterItem>
        <FilterItem label="Tiến độ dòng">
          <SearchSelect value={f.state} placeholder="Tất cả"
            options={states.map((s) => ({ value: s, label: s }))}
            onChange={(v) => setFilter('state', v)} />
        </FilterItem>
        <FilterItem label="Trễ hạn" width={170}>
          <select value={f.late} onChange={(e) => setFilter('late', e.target.value)}>
            <option value="">Không lọc</option>
            <option value="1">Chỉ dòng trễ hạn</option>
          </select>
        </FilterItem>
        <FilterItem label="Ngày tiếp nhận" width={260} active={!!(f.received_date_from || f.received_date_to)}>
          <DateRangePicker block value={{ from: f.received_date_from, to: f.received_date_to }}
            onChange={(v) => { setF((s: any) => ({ ...s, received_date_from: v.from, received_date_to: v.to })); setPage(1) }} />
        </FilterItem>
        <FilterItem label="Tìm kiếm" grow>
          <input value={f.q} placeholder="Mã YCBG / mục đích / phân loại / thông số…"
            onChange={(e) => setFilter('q', e.target.value)} />
        </FilterItem>
      </FilterPanel>
      </ConditionalFilter>

      <div className="card table-card">
        <TableToolbar {...table} onRefresh={load} />
        <TableScroll>
          <table className="dense" style={{ minWidth: minW, tableLayout: 'fixed' }}>
            <TableColGroup columns={table.columns} colW={table.colW} />
            <TableHead columns={table.columns} startResize={table.startResize}
              sortBy={sortBy} sortDir={sortDir} onSort={handleSort} />
            <tbody>
              {rows.map((r, i) => (
                <tr key={`${r.line_id}-${i}`}>
                  <TableCells columns={table.columns} row={r} index={i} />
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan={table.columns.length} className="table-empty">Chưa có dữ liệu tiến độ</td></tr>}
            </tbody>
          </table>
        </TableScroll>
        <div className="table-foot">
          <Pagination page={page} pageSize={pageSize} total={total}
            onChange={(p, s) => { setPage(p); setPageSize(s) }} />
        </div>
      </div>
      <div style={{ marginTop: 8, fontSize: 12.5, color: 'var(--muted)' }}>
        * Mỗi dòng = 1 dòng yêu cầu trên phiếu báo giá. Cột "Trễ (ngày)" tính theo ngày trả kết
        quả thực tế; dòng chưa trả mà đã quá hạn vẫn được tính tới hôm nay.
        {!showSupplier && ' Cột nhà cung cấp được ẩn theo quyền của bạn.'}
      </div>
    </div>
  )
}
