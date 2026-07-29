import { useEffect, useState } from 'react'
import { api } from '../api/client'
import Pagination from '../components/Pagination'
import { poBadge } from '../config/cruds'
import SearchSelect from '../components/SearchSelect'
import MatrixPivotTab from '../components/MatrixPivotTab'
import { ReportTable, fmt, pctv } from '../components/report-table'
import { useAuth } from '../auth/AuthContext'

const TABS = [
  { key: 'overview', label: 'Tổng quan' },
  { key: 'supplier', label: 'Nhà cung cấp', need: 'purchase_order' },   // NCC nhạy cảm -> ẩn với phòng ban YC (không có quyền xem ĐMH)
  { key: 'item_group', label: 'Phân loại vật tư bao bì / nguyên liệu' },
  { key: 'nspt', label: 'Nhân sự phụ trách', need: 'purchase_order' },        // phía thu mua -> ẩn với phòng ban YC
  { key: 'department', label: 'Bộ phận (đơn gấp)' },                          // phòng ban YC chỉ thấy phòng mình (scope BE)
  { key: 'shipping', label: 'Chi phí vận chuyển', need: 'purchase_order' },   // phía thu mua -> ẩn với phòng ban YC
  { key: 'pyc_req', label: 'Yêu cầu mua hàng', need: 'purchase_request' },   // theo phòng ban
  { key: 'ycks_req', label: 'Yêu cầu báo giá', need: 'survey_request' },    // theo phòng ban
  // { key: 'inventory', label: 'Tồn kho' },   // tạm ẩn tab Tồn kho
]

// Cột trạng thái cho báo cáo yêu cầu — khớp enum thật trong DB (Tổng = tổng các cột)
const PYC_METRICS = [
  { key: 'total', label: 'Tổng' }, { key: 'draft', label: 'Nháp' }, { key: 'submitted', label: 'Chờ duyệt' },
  { key: 'approved', label: 'Đã duyệt' }, { key: 'processing', label: 'Đang xử lý' }, { key: 'completed', label: 'Hoàn tất' },
  { key: 'rejected', label: 'Từ chối' }, { key: 'cancelled', label: 'Đã hủy' },
]
const YCKS_METRICS = [
  { key: 'total', label: 'Tổng' }, { key: 'draft', label: 'Nháp' }, { key: 'submitted', label: 'Chờ duyệt' },
  { key: 'processing', label: 'Đang khảo sát' }, { key: 'survey_done', label: 'Đã khảo sát' }, { key: 'pr_created', label: 'Đã tạo yêu cầu mua hàng' },
  { key: 'done', label: 'Hoàn tất' }, { key: 'cancelled', label: 'Đã hủy' },
]

const shortNum = (n: any) => {
  n = Number(n || 0)
  if (n >= 1e9) return (n / 1e9).toFixed(1).replace('.0', '') + ' tỷ'
  if (n >= 1e6) return (n / 1e6).toFixed(1).replace('.0', '') + ' tr'
  if (n >= 1e3) return Math.round(n / 1e3) + 'k'
  return String(n)
}
// Biểu đồ cột có trục X/Y + lưới; hover hiện số tiền, click cột -> onBar(item)
function BarChart({ data, color, onBar }: { data: any[]; color?: string; onBar?: (m: any) => void }) {
  const [hi, setHi] = useState<number | null>(null)
  if (!data.length) return <span style={{ color: '#999' }}>Chưa có dữ liệu.</span>
  const max = Math.max(1, ...data.map((x) => x.amount))
  const H = 160
  const ticks = [1, 0.75, 0.5, 0.25, 0]
  return (
    <div style={{ display: 'flex', gap: 4 }}>
      <div style={{ width: 52, height: H, position: 'relative', flex: 'none' }}>
        {ticks.map((t) => (
          <div key={t} style={{ position: 'absolute', right: 4, top: `${(1 - t) * 100}%`, transform: 'translateY(-50%)', fontSize: 9.5, color: 'var(--muted)' }}>{shortNum(max * t)}</div>
        ))}
      </div>
      <div style={{ overflowX: 'auto', flex: 1 }}>
        <div style={{ position: 'relative', height: H, borderLeft: '1px solid #cbd5e1', borderBottom: '1px solid #cbd5e1', minWidth: data.length * 44 }}>
          {ticks.map((t) => <div key={t} style={{ position: 'absolute', left: 0, right: 0, top: `${(1 - t) * 100}%`, borderTop: '1px dashed #edf1f5' }} />)}
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'flex-end', gap: 14, padding: '0 12px' }}>
            {data.map((m, i) => (
              <div key={i} onMouseEnter={() => setHi(i)} onMouseLeave={() => setHi(null)}
                   onClick={() => m.amount && onBar && onBar(m)}
                   style={{ width: 30, flex: 'none', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', height: '100%', position: 'relative', cursor: m.amount && onBar ? 'pointer' : 'default' }}>
                {hi === i && (
                  <div style={{ position: 'absolute', bottom: '100%', left: '50%', transform: 'translateX(-50%)', marginBottom: 4, background: 'var(--navy)', color: '#fff', fontSize: 10.5, padding: '3px 6px', borderRadius: 5, whiteSpace: 'nowrap', zIndex: 5 }}>
                    {m.month}: {fmt(m.amount)}
                  </div>
                )}
                <div style={{ background: m.amount ? (color || 'var(--teal)') : '#e6ebf0', borderRadius: '3px 3px 0 0', height: `${(m.amount / max) * 100}%`, minHeight: m.amount ? 4 : 2, outline: hi === i ? '2px solid var(--navy)' : 'none' }} />
              </div>
            ))}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 14, padding: '4px 12px', minWidth: data.length * 44 }}>
          {data.map((m, i) => <div key={i} style={{ width: 30, flex: 'none', textAlign: 'center', fontSize: 9.5, color: 'var(--muted)' }}>{m.month.slice(0, 2)}</div>)}
        </div>
      </div>
    </div>
  )
}

// Biểu đồ đường (SVG) — chi phí theo ngày
function LineChart({ days }: { days: any[] }) {
  if (!days.length) return <div style={{ color: '#999', padding: 20, textAlign: 'center' }}>Không có phát sinh trong tháng này.</div>
  const W = 620, H = 240, pl = 56, pr = 12, pt = 12, pb = 28
  const max = Math.max(1, ...days.map((d) => d.amount))
  const n = days.length
  const X = (i: number) => pl + (n <= 1 ? (W - pl - pr) / 2 : (i / (n - 1)) * (W - pl - pr))
  const Y = (v: number) => pt + (1 - v / max) * (H - pt - pb)
  const pts = days.map((d, i) => `${X(i)},${Y(d.amount)}`).join(' ')
  const areaPts = `${X(0)},${H - pb} ${pts} ${X(n - 1)},${H - pb}`
  const ticks = [1, 0.75, 0.5, 0.25, 0]
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%' }}>
      <defs>
        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--teal)" stopOpacity="0.28" />
          <stop offset="100%" stopColor="var(--teal)" stopOpacity="0" />
        </linearGradient>
      </defs>
      {ticks.map((t) => (
        <g key={t}>
          <line x1={pl} y1={pt + (1 - t) * (H - pt - pb)} x2={W - pr} y2={pt + (1 - t) * (H - pt - pb)} stroke="#edf1f5" />
          <text x={pl - 6} y={pt + (1 - t) * (H - pt - pb) + 3} textAnchor="end" fontSize="9.5" fill="#8a97a5">{shortNum(max * t)}</text>
        </g>
      ))}
      <line x1={pl} y1={pt} x2={pl} y2={H - pb} stroke="#cbd5e1" />
      <line x1={pl} y1={H - pb} x2={W - pr} y2={H - pb} stroke="#cbd5e1" />
      <polygon points={areaPts} fill="url(#areaGrad)" />
      <polyline points={pts} fill="none" stroke="var(--teal)" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
      {days.map((d, i) => (
        <g key={i}>
          <circle cx={X(i)} cy={Y(d.amount)} r="3.5" fill="var(--teal)"><title>{`Ngày ${d.day}: ${fmt(d.amount)}`}</title></circle>
          <text x={X(i)} y={H - pb + 14} textAnchor="middle" fontSize="9" fill="#8a97a5">{d.day}</text>
        </g>
      ))}
    </svg>
  )
}

export default function Reports() {
  const thisYear = new Date().getFullYear()
  const { can } = useAuth()
  const tabs = TABS.filter((t) => !t.need || can(t.need, 'read'))   // gate tab YC theo quyền
  const [d, setD] = useState<any>(null)
  const [mx, setMx] = useState<any>(null)
  const [companies, setCompanies] = useState<any[]>([])
  const [f, setF] = useState<any>({ year: String(thisYear), company_id: '' })
  const [tab, setTab] = useState('overview')
  const [period, setPeriod] = useState('all')   // 'all' | 'YYYY-MM'
  const [busy, setBusy] = useState(false)
  const [daily, setDaily] = useState<any>(null)  // {month, label, data} popup chi tiết theo ngày
  const [shipF, setShipF] = useState({ carrier: '', month: '' })  // lọc chi tiết VC theo đơn vị VC + tháng
  const [shipPage, setShipPage] = useState(1)                     // phân trang chi tiết VC (server, 50/trang)
  const [shipData, setShipData] = useState<any>({ items: [], total: 0, carriers: [], months: [], page: 1, page_size: 50 })
  const [reqMx, setReqMx] = useState<Record<string, any>>({})   // cache báo cáo YC: key `kind|year|company` -> {months,rows}
  const [xlsMenu, setXlsMenu] = useState(false)   // popup chọn báo cáo để xuất Excel

  // Xuất Excel 1 form (hoặc tất cả) — khớp form thumua1 sheet 12–16. Luôn theo 1 năm cụ thể.
  async function exportExcel(sheet: string) {
    setXlsMenu(false)
    const year = f.year === 'all' ? String(thisYear) : String(f.year)
    const params: any = { sheet, year }
    if (f.company_id) params.company_id = f.company_id
    try {
      const r = await api.get('/api/reports/export', { params, responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([r.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `bao-cao-mua-hang-${sheet}-${year}.xlsx`)
      document.body.appendChild(link); link.click(); link.remove()
      window.URL.revokeObjectURL(url)
    } catch { /* interceptor tự toast lỗi */ }
  }

  // Tải ma trận Yêu cầu (PYC/YCKS) khi vào tab tương ứng (live + scope server)
  useEffect(() => {
    const kind = tab === 'pyc_req' ? 'pyc' : tab === 'ycks_req' ? 'ycks' : null
    if (!kind) return
    const key = `${kind}|${f.year}|${f.company_id}`
    if (reqMx[key]) return
    const params: any = { kind }
    if (f.year) params.year = f.year
    if (f.company_id) params.company_id = f.company_id
    api.get('/api/reports/request-matrix', { params }).then((r) => setReqMx((s) => ({ ...s, [key]: r.data.data })))
  }, [tab, f.year, f.company_id])

  // Chi tiết chi phí vận chuyển: phân trang phía server (50/trang) — tránh tải full lag trang
  useEffect(() => {
    if (tab !== 'shipping') return
    const params: any = { page: shipPage, page_size: 50 }
    if (f.year) params.year = f.year
    if (f.company_id) params.company_id = f.company_id
    if (shipF.carrier) params.carrier = shipF.carrier
    if (shipF.month) params.month = shipF.month
    api.get('/api/reports/shipping-detail', { params }).then((r) => setShipData(r.data.data)).catch(() => {})
  }, [tab, f.year, f.company_id, shipF.carrier, shipF.month, shipPage])

  async function openDaily(m: any) {
    setDaily({ month: m.monthKey, label: m.month, data: null })
    const params: any = { month: m.monthKey }
    if (f.company_id) params.company_id = f.company_id
    const r = await api.get('/api/reports/daily', { params })
    setDaily({ month: m.monthKey, label: m.month, data: r.data.data })
  }

  async function load(refresh = false) {
    setBusy(true)
    const params: any = {}
    if (f.year) params.year = f.year
    if (f.company_id) params.company_id = f.company_id
    const procParams = { ...params, ...(period !== 'all' ? { month: period } : {}) }   // giữ lọc phụ theo tháng khi bấm Lọc
    try {
      const [a, b] = await Promise.all([
        api.get('/api/reports/procurement', { params: procParams }),
        api.get('/api/reports/matrix', { params: { ...params, ...(refresh ? { refresh: 1 } : {}) } }),
      ])
      setD(a.data.data); setMx(b.data.data)
      setShipF({ carrier: '', month: '' })   // reset lọc chi tiết VC theo data mới
    } finally { setBusy(false) }
  }
  useEffect(() => {
    api.get('/api/companies', { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items))
    load()
  }, [])

  // Tab Tổng quan — lọc phụ theo THÁNG (áp dụng ngay như "Xem theo:" các tab khác).
  // Chỉ nạp lại số liệu tổng quan; year/company vẫn dùng giá trị đang áp dụng. Bỏ qua lần đầu (đợi load()).
  useEffect(() => {
    if (tab !== 'overview' || !d) return
    const params: any = {}
    if (f.year) params.year = f.year
    if (f.company_id) params.company_id = f.company_id
    if (period !== 'all') params.month = period
    api.get('/api/reports/procurement', { params }).then((r) => setD(r.data.data)).catch(() => {})
  }, [tab, period])
  if (!d || !mx) return <div style={{ padding: 20 }}>Đang tải...</div>
  const months = mx.months || []

  const shipPages = Math.max(1, Math.ceil((shipData.total || 0) / (shipData.page_size || 50)))

  const Card = ({ label, val, sub, color }: any) => (
    <div className="card" style={{ padding: 16, flex: 1, minWidth: 165 }}>
      <div style={{ fontSize: 12.5, color: 'var(--muted)' }}>{label}</div>
      <div style={{ fontSize: 21, fontWeight: 700, color: color || 'var(--navy)' }}>{val}</div>
      {sub && <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>{sub}</div>}
    </div>
  )
  const Bars = ({ rows, label, value, color }: any) => {
    const max = Math.max(1, ...rows.map((r: any) => r[value]))
    return rows.map((r: any, i: number) => (
      <div key={i} style={{ marginBottom: 8 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5 }}>
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '62%' }}>{r[label]}</span><b>{fmt(r[value])}</b></div>
        <div style={{ height: 10, background: '#eef2f6', borderRadius: 6, overflow: 'hidden' }}><div style={{ width: `${(r[value] / max) * 100}%`, height: '100%', background: color || 'var(--teal)' }} /></div>
      </div>
    ))
  }
  const periodLabel = period === 'all' ? 'Cả năm' : months.find((m: any) => m.key === period)?.label || period
  // Chi phí theo tháng: đủ 12 cột của năm (tháng trống = 0)
  const spendMap: Record<string, number> = Object.fromEntries((d.spend_by_month || []).map((m: any) => [m.month, m.amount]))
  const spendSeries = months.map((m: any) => ({ monthKey: m.key, month: m.label, amount: spendMap[m.key] || 0 }))

  const del = d.delivery || { on_time: 0, late: 0, total: 0 }
  const onTimePct = del.total ? Math.round((del.on_time / del.total) * 100) : 0
  const remaining = (d.payable_goods.remaining || 0) + (d.payable_shipping.remaining || 0)

  return (
    <div>
      <div className="no-print" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
        <h2 className="page-title" style={{ margin: 0 }}>Báo cáo mua hàng</h2>
        <div className="filters" style={{ display: 'flex', gap: 10, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div style={{ minWidth: 180 }}><label style={{ fontSize: 12, color: 'var(--muted)' }}>Công ty</label>
            <SearchSelect value={f.company_id} placeholder="Tất cả"
              options={companies.map((c) => ({ value: String(c.id), label: c.name }))}
              onChange={(v) => { setShipPage(1); setF((s: any) => ({ ...s, company_id: v })) }} /></div>
          <div style={{ minWidth: 120 }}><label style={{ fontSize: 12, color: 'var(--muted)' }}>Năm</label>
            <SearchSelect value={String(f.year)} placeholder="Tất cả"
              options={[{ value: 'all', label: 'Tất cả' }, ...[thisYear, thisYear - 1, thisYear - 2].map((y) => ({ value: String(y), label: String(y) }))]}
              onChange={(v) => { setShipPage(1); setF((s: any) => ({ ...s, year: v })) }} /></div>
          <button className="btn" disabled={busy} onClick={() => load(false)}>Lọc</button>
          <button className="btn secondary" disabled={busy} onClick={() => load(true)} title="Tính lại số liệu báo cáo"><i className="ti ti-refresh" />Cập nhật</button>
          <button className="btn ghost" onClick={() => window.print()}><i className="ti ti-printer" />In</button>
          {can('report', 'export') && (
            <div style={{ position: 'relative' }}>
              <button className="btn ghost" onClick={() => setXlsMenu((v) => !v)} title="Xuất báo cáo ra Excel">
                <i className="ti ti-file-spreadsheet" />Xuất Excel<i className="ti ti-chevron-down" style={{ marginLeft: 4 }} />
              </button>
              {xlsMenu && (
                <>
                  <div style={{ position: 'fixed', inset: 0, zIndex: 20 }} onClick={() => setXlsMenu(false)} />
                  <div style={{ position: 'absolute', right: 0, top: '100%', marginTop: 4, zIndex: 21, background: '#fff', border: '1px solid var(--border)', borderRadius: 8, boxShadow: '0 6px 20px rgba(0,0,0,.12)', minWidth: 230, overflow: 'hidden' }}>
                    {[
                      { sheet: 'all', label: 'Tất cả (5 báo cáo)', icon: 'ti-stack-2' },
                      { sheet: 'nspt', label: 'Nhân sự phụ trách', icon: 'ti-user' },
                      { sheet: 'item_group', label: 'Phân loại VTBB/NL', icon: 'ti-package' },
                      { sheet: 'supplier', label: 'Nhà cung cấp', icon: 'ti-building-store' },
                      { sheet: 'department', label: 'Bộ phận (đơn gấp)', icon: 'ti-users' },
                      { sheet: 'shipping', label: 'Chi phí vận chuyển', icon: 'ti-truck' },
                    ].map((o, i) => (
                      <button key={o.sheet} onClick={() => exportExcel(o.sheet)}
                        style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%', border: 'none', borderTop: i === 1 ? '1px solid var(--border)' : 'none', background: 'none', padding: '9px 14px', cursor: 'pointer', fontSize: 13.5, textAlign: 'left', fontWeight: o.sheet === 'all' ? 700 : 500 }}
                        onMouseEnter={(e) => (e.currentTarget.style.background = '#f4f6f8')}
                        onMouseLeave={(e) => (e.currentTarget.style.background = 'none')}>
                        <i className={`ti ${o.icon}`} />{o.label}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="no-print" style={{ display: 'flex', gap: 6, flexWrap: 'nowrap', overflowX: 'auto', marginBottom: 8, borderBottom: '1px solid var(--border)' }}>
        {tabs.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)} style={{ border: 'none', background: 'none', padding: '8px 12px', cursor: 'pointer', fontSize: 13.5, fontWeight: tab === t.key ? 700 : 500, color: tab === t.key ? 'var(--teal)' : 'var(--muted)', borderBottom: tab === t.key ? '2px solid var(--teal)' : '2px solid transparent', whiteSpace: 'nowrap', flexShrink: 0 }}>{t.label}</button>
        ))}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, marginBottom: 10 }}>
        <div style={{ fontSize: 12, color: 'var(--muted)' }}>Kỳ: {f.year === 'all' ? 'Tất cả' : `Năm ${f.year}`} · {f.company_id ? companies.find((c) => String(c.id) === String(f.company_id))?.name : 'Tất cả công ty'} · Tính lúc: {mx.computed_at}</div>
        {(tab === 'overview' || tab === 'shipping') && (
          <div className="no-print" style={{ fontSize: 12.5, display: 'flex', alignItems: 'center', gap: 6 }}>Xem theo:
            <div style={{ minWidth: 150 }}>
              <SearchSelect value={period} placeholder="Cả năm"
                options={[{ value: 'all', label: 'Cả năm' }, ...months.map((m: any) => ({ value: m.key, label: m.label }))]}
                onChange={(v) => setPeriod(v)} />
            </div>
          </div>
        )}
      </div>

      {tab === 'overview' && (<>
        <div className="no-print" style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 10, background: '#f6f8fa', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 12px', lineHeight: 1.55 }}>
          <i className="ti ti-info-circle" style={{ marginRight: 5, color: 'var(--teal)' }} />
          <b>Lưu ý cách đọc số:</b> "Giá trị đặt hàng" = tổng giá trị các đơn <b>ĐẶT</b> theo <b>ngày đặt</b>. Biểu đồ "Chi phí mua theo tháng" = <b>công nợ phát sinh</b> (tiền hàng + vận chuyển, gồm VAT, theo lượng thực nhận) theo <b>ngày nhận hàng</b>. Hai con số đo khác nhau nên <b>không bằng nhau</b>. Mọi số liệu chỉ tính <b>đơn thật</b> (đã duyệt trở đi) — đã loại trừ đơn nháp / chờ duyệt / hủy / từ chối.
          {period !== 'all' && <><br /><i className="ti ti-filter" style={{ marginRight: 4 }} />Đang lọc theo <b>{periodLabel}</b>: các thẻ số &amp; tình hình đơn/giao hàng tính theo tháng này; riêng biểu đồ "Chi phí mua theo tháng" vẫn hiển thị cả năm.</>}
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 14 }}>
          <Card label="Số đơn mua hàng" val={fmt(d.po_count)} />
          <Card label="Giá trị đặt hàng" val={fmt(d.order_value)} color="var(--teal)" />
          <Card label="Công nợ còn phải trả" val={fmt(remaining)} sub={`Hàng ${fmt(d.payable_goods.remaining)} · Vận chuyển ${fmt(d.payable_shipping.remaining)}`} />
          <Card label="Công nợ quá hạn" val={fmt(d.overdue)} color="var(--red)" />
          <Card label="Giá trị tồn kho" val={fmt(d.inventory_value)} color="var(--green)" />
        </div>
        <div className="grid-2">
          <div className="card" style={{ padding: 18 }}>
            <h3 className="sec-title">Đơn theo trạng thái</h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
              {Object.entries(d.po_status).filter(([, v]: any) => v > 0).map(([k, v]: any) => (
                <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 6, border: '1px solid var(--border)', borderRadius: 8, padding: '6px 10px' }}>{poBadge(k)} <b>{v}</b></div>))}
              {d.po_count === 0 && <span style={{ color: '#999' }}>Chưa có đơn.</span>}
            </div>
            <h3 className="sec-title" style={{ marginTop: 18 }}>Tiến độ giao hàng</h3>
            <div style={{ fontSize: 13, marginBottom: 6 }}>Đúng hạn <b style={{ color: 'var(--green)' }}>{del.on_time}</b> · Trễ <b style={{ color: 'var(--red)' }}>{del.late}</b> / {del.total}</div>
            <div style={{ height: 14, background: '#fde2e2', borderRadius: 8, overflow: 'hidden' }}><div style={{ width: `${onTimePct}%`, height: '100%', background: 'var(--green)' }} /></div>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>Đúng hạn {onTimePct}%</div>
          </div>
          <div className="card" style={{ padding: 18 }}>
            <h3 className="sec-title">Chi phí mua theo tháng <span style={{ fontSize: 11.5, fontWeight: 400, color: 'var(--muted)' }}>(công nợ phát sinh theo ngày nhận · rê xem số tiền · bấm cột để xem theo ngày)</span></h3>
            <BarChart data={spendSeries} color="var(--teal)" onBar={openDaily} />
          </div>
        </div>
      </>)}

      {tab === 'supplier' && (
        <MatrixPivotTab key={`sup-${f.year}-${f.company_id}`}
          rows={mx.supplier || []} months={months} companyId={f.company_id} nameWidth={260} nameFilter
          nameLabel="Nhà cung cấp" title="Giao dịch nhà cung cấp" warnHint="đỏ = tỷ lệ trễ > 30%"
          yearLabel={f.year === 'all' ? 'Tất cả' : `Năm ${f.year}`} rangeEndpoint="/api/reports/sup-range"
          metrics={[{ key: 'trans', label: 'Số lần giao dịch' }, { key: 'late', label: 'Số lần trễ' }, { key: 'rate', label: 'Tỷ lệ trễ', pct: true }]} />
      )}

      {tab === 'item_group' && (
        <MatrixPivotTab key={`ig-${f.year}-${f.company_id}`}
          rows={mx.item_group || []} months={months} companyId={f.company_id} nameWidth={200} nameFilter
          nameLabel="Loại vật tư bao bì / nguyên liệu" title="Tần suất mua theo loại vật tư bao bì / nguyên liệu"
          yearLabel={f.year === 'all' ? 'Tất cả' : `Năm ${f.year}`} rangeEndpoint="/api/reports/ig-range"
          metrics={[{ key: 'trans', label: 'Số lần mua' }, { key: 'cost', label: 'Tổng chi phí mua' }]} />
      )}

      {tab === 'nspt' && (
        <MatrixPivotTab key={`nspt-${f.year}-${f.company_id}`}
          rows={mx.nspt || []} months={months} companyId={f.company_id}
          nameLabel="Nhân sự phụ trách" title="Giao hàng theo nhân sự phụ trách" warnHint="đỏ = tỷ lệ trễ > 30%"
          yearLabel={f.year === 'all' ? 'Tất cả' : `Năm ${f.year}`} rangeEndpoint="/api/reports/nspt-range"
          metrics={[{ key: 'orders', label: 'Số lần giao' }, { key: 'late', label: 'Trễ quy định' }, { key: 'ontime', label: 'Đúng hạn' }, { key: 'early', label: 'Giao sớm' }, { key: 'rate', label: 'Tỷ lệ trễ', pct: true }]} />
      )}

      {tab === 'department' && (
        <MatrixPivotTab key={`dept-${f.year}-${f.company_id}`}
          rows={mx.department || []} months={months} companyId={f.company_id} nameFilter
          nameLabel="Bộ phận" title="Đặt hàng & đơn gấp theo bộ phận" warnHint="đỏ = tỷ lệ gấp > 30%"
          yearLabel={f.year === 'all' ? 'Tất cả' : `Năm ${f.year}`} rangeEndpoint="/api/reports/dept-range"
          metrics={[{ key: 'orders', label: 'Số lần đặt' }, { key: 'urgent', label: 'Số lần gấp' }, { key: 'rate', label: 'Tỷ lệ gấp', pct: true }]} />
      )}

      {(tab === 'pyc_req' || tab === 'ycks_req') && (() => {
        const kind = tab === 'pyc_req' ? 'pyc' : 'ycks'
        const rmx = reqMx[`${kind}|${f.year}|${f.company_id}`]
        if (!rmx) return <div className="card" style={{ padding: 16, color: '#999' }}>Đang tải…</div>
        return (
          <MatrixPivotTab key={`${kind}-${f.year}-${f.company_id}`}
            rows={rmx.rows || []} months={rmx.months || []} companyId={f.company_id} nameFilter nameWidth={220}
            nameLabel="Phòng ban"
            title={kind === 'pyc' ? 'Yêu cầu mua hàng theo phòng ban' : 'Yêu cầu báo giá theo phòng ban'}
            yearLabel={f.year === 'all' ? 'Tất cả' : `Năm ${f.year}`}
            rangeEndpoint={`/api/reports/request-range?kind=${kind}`}
            metrics={kind === 'pyc' ? PYC_METRICS : YCKS_METRICS} />
        )
      })()}

      {tab === 'shipping' && <>
        <div className="card" style={{ padding: 16, marginBottom: 14 }}>
          <h3 className="sec-title">Chi phí vận chuyển theo đơn vị vận chuyển — {periodLabel} <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--muted)' }}>(Tỷ lệ = Chi phí vận chuyển / Giá trị đơn hàng)</span></h3>
          <ReportTable rows={mx.shipping} period={period} nameLabel="Đơn vị vận chuyển"
            metrics={[{ key: 'freq', label: 'Tần suất' }, { key: 'order_value', label: 'Giá trị đơn hàng' }, { key: 'ship_cost', label: 'Chi phí vận chuyển' }, { key: 'rate', label: 'Tỷ lệ', pct: true }]} />
        </div>
        <div className="card" style={{ padding: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, marginBottom: 10 }}>
            <h3 className="sec-title" style={{ margin: 0 }}>Chi tiết theo đơn hàng</h3>
            <div className="no-print" style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: 'var(--muted)' }}>Lọc:
              <div style={{ minWidth: 180 }}>
                <SearchSelect value={shipF.carrier} placeholder="Tất cả đơn vị vận chuyển"
                  options={[{ value: '', label: 'Tất cả đơn vị vận chuyển' }, ...(shipData.carriers || []).map((c: string) => ({ value: c, label: c }))]}
                  onChange={(v) => { setShipPage(1); setShipF((s) => ({ ...s, carrier: v })) }} />
              </div>
              <div style={{ minWidth: 130 }}>
                <SearchSelect value={shipF.month} placeholder="Tất cả tháng"
                  options={[{ value: '', label: 'Tất cả tháng' }, ...(shipData.months || []).map((m: string) => ({ value: m, label: m }))]}
                  onChange={(v) => { setShipPage(1); setShipF((s) => ({ ...s, month: v })) }} />
              </div>
            </div>
          </div>
          <div className="items-scroll">
            <table className="items-table" style={{ minWidth: 1000 }}>
              <thead><tr><th>Đơn vị vận chuyển</th><th>Tháng</th><th>Mã vật tư bao bì / nguyên liệu</th><th>Mã MISA</th><th>Số hóa đơn</th><th>Ngày nhận</th><th style={{ textAlign: 'right' }}>Số lượng đặt</th><th style={{ textAlign: 'right' }}>Số lượng nhận</th><th style={{ textAlign: 'right' }}>Thành tiền đơn hàng</th><th style={{ textAlign: 'right' }}>Thành tiền vận chuyển</th><th style={{ textAlign: 'right' }}>Tỷ lệ</th></tr></thead>
              <tbody>
                {(shipData.items || []).map((r: any, i: number) => (
                  <tr key={i}><td>{r.carrier}</td><td>{r.month}</td><td>{r.product_code}</td><td>{r.misa_code}</td><td>{r.invoice_no}</td><td>{r.received_date}</td>
                    <td style={{ textAlign: 'right' }}>{fmt(r.qty_order)}</td><td style={{ textAlign: 'right' }}>{fmt(r.qty_received)}</td>
                    <td style={{ textAlign: 'right' }}>{fmt(r.order_amount)}</td><td style={{ textAlign: 'right' }}>{fmt(r.ship_amount)}</td><td style={{ textAlign: 'right' }}>{pctv(r.rate)}</td></tr>))}
                {(shipData.total || 0) === 0 && <tr><td colSpan={11} style={{ textAlign: 'center', color: '#999', padding: 14 }}>{(shipF.carrier || shipF.month) ? 'Không có dòng khớp bộ lọc' : 'Chưa có chi phí vận chuyển'}</td></tr>}
              </tbody>
            </table>
          </div>
          {shipData.total > 0 && (
            <div className="no-print" style={{ marginTop: 10 }}>
              <Pagination page={shipData.page} pageSize={shipData.page_size} total={shipData.total}
                hideSize onChange={(p) => setShipPage(p)} />
            </div>
          )}
        </div>
      </>}

      {tab === 'inventory' && <>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 14 }}><Card label="Tổng giá trị tồn" val={fmt(d.inventory.total)} color="var(--green)" /></div>
        <div className="grid-1-2">
          <div className="card" style={{ padding: 18 }}>
            <h3 className="sec-title">Giá trị tồn theo kho</h3>
            <Bars rows={d.inventory.by_warehouse} label="warehouse" value="value" color="var(--green)" />
            {d.inventory.by_warehouse.length === 0 && <span style={{ color: '#999' }}>Chưa có tồn.</span>}
          </div>
          <div className="card" style={{ padding: 18 }}>
            <h3 className="sec-title">Top sản phẩm theo giá trị tồn</h3>
            <div className="items-scroll">
              <table className="items-table" style={{ minWidth: 640 }}>
                <thead><tr><th>Mã SP</th><th>Tên</th><th>Kho</th><th style={{ textAlign: 'right' }}>Tồn</th><th style={{ textAlign: 'right' }}>Đơn giá BQ</th><th style={{ textAlign: 'right' }}>Giá trị</th></tr></thead>
                <tbody>
                  {d.inventory.top.map((r: any, i: number) => (
                    <tr key={i}><td>{r.product_code}</td><td>{r.product_name}</td><td>{r.warehouse}</td>
                      <td style={{ textAlign: 'right' }}>{fmt(r.qty)}</td><td style={{ textAlign: 'right' }}>{fmt(r.avg_cost)}</td><td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(r.value)}</td></tr>))}
                  {d.inventory.top.length === 0 && <tr><td colSpan={6} style={{ textAlign: 'center', color: '#999', padding: 14 }}>Chưa có tồn</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </>}

      {/* Popup chi phí theo ngày (click cột tháng) */}
      {daily && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.45)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
          <div className="modal-card" style={{ width: 680, maxWidth: '100%', background: '#fff', borderRadius: 12, maxHeight: '88vh', overflow: 'auto' }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', borderBottom: '1px solid var(--border)' }}>
              <h3 style={{ margin: 0, fontSize: 16, color: 'var(--navy)' }}>Chi phí theo ngày — {daily.label}{daily.data ? ` · Tổng ${fmt(daily.data.total)}` : ''}</h3>
              <button className="icon-btn" onClick={() => setDaily(null)}><i className="ti ti-x" style={{ fontSize: 18 }} /></button>
            </div>
            <div style={{ padding: 16 }}>
              {!daily.data ? <div style={{ padding: 20, textAlign: 'center', color: 'var(--muted)' }}>Đang tải...</div> : (<>
                <LineChart days={daily.data.days} />
                <div className="items-scroll" style={{ marginTop: 12 }}>
                  <table className="items-table" style={{ minWidth: 420 }}>
                    <thead><tr><th>Ngày</th><th style={{ textAlign: 'right' }}>Hàng hóa</th><th style={{ textAlign: 'right' }}>Vận chuyển</th><th style={{ textAlign: 'right' }}>Tổng</th></tr></thead>
                    <tbody>
                      {daily.data.days.map((r: any, i: number) => (
                        <tr key={i}><td>{r.date}</td><td style={{ textAlign: 'right' }}>{fmt(r.goods)}</td><td style={{ textAlign: 'right' }}>{fmt(r.shipping)}</td><td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(r.amount)}</td></tr>
                      ))}
                      {daily.data.days.length === 0 && <tr><td colSpan={4} style={{ textAlign: 'center', color: '#999', padding: 14 }}>Không có phát sinh</td></tr>}
                    </tbody>
                  </table>
                </div>
              </>)}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
