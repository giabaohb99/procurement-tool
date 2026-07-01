import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { poBadge } from '../config/cruds'

const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
const pctv = (n: any) => `${Number(n || 0).toLocaleString('vi-VN')}%`

const TABS = [
  { key: 'overview', label: 'Tổng quan' },
  { key: 'supplier', label: 'NCC (trễ giao)' },
  { key: 'item_group', label: 'Phân loại VTBB/NL' },
  { key: 'nspt', label: 'NSPT' },
  { key: 'department', label: 'Bộ phận (đơn gấp)' },
  { key: 'shipping', label: 'Chi phí vận chuyển' },
  { key: 'inventory', label: 'Tồn kho' },
]
type Metric = { key: string; label: string; pct?: boolean }

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

// Bảng báo cáo gọn: dòng = đối tượng, cột = chỉ số (theo kỳ đã chọn)
function ReportTable({ rows, metrics, period, warnMetric, nameLabel }:
  { rows: any[]; metrics: Metric[]; period: string; warnMetric?: string; nameLabel: string }) {
  const val = (r: any, k: string) => (period === 'all' ? (r[k] ?? 0) : (r.m?.[period]?.[k] ?? 0))
  return (
    <div className="items-scroll">
      <table className="items-table" style={{ minWidth: 480 }}>
        <thead><tr><th style={{ width: 40 }}>#</th><th style={{ textAlign: 'left', minWidth: 160 }}>{nameLabel}</th>
          {metrics.map((m) => <th key={m.key} style={{ textAlign: 'right' }}>{m.label}</th>)}</tr></thead>
        <tbody>
          {rows.map((r, i) => {
            const warn = warnMetric ? Number(val(r, warnMetric)) > 30 : false
            return (
              <tr key={i} style={warn ? { background: '#fdecea' } : {}}>
                <td>{i + 1}</td><td style={{ textAlign: 'left', fontWeight: 500 }}>{r.key}</td>
                {metrics.map((m) => (
                  <td key={m.key} style={{ textAlign: 'right', fontWeight: m.key === warnMetric ? 600 : 400, color: (m.key === warnMetric && warn) ? 'var(--red)' : 'inherit' }}>
                    {m.pct ? pctv(val(r, m.key)) : fmt(val(r, m.key))}
                  </td>
                ))}
              </tr>
            )
          })}
          {rows.length === 0 && <tr><td colSpan={2 + metrics.length} style={{ textAlign: 'center', color: '#999', padding: 14 }}>Không có dữ liệu</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

export default function Reports() {
  const thisYear = new Date().getFullYear()
  const [d, setD] = useState<any>(null)
  const [mx, setMx] = useState<any>(null)
  const [companies, setCompanies] = useState<any[]>([])
  const [f, setF] = useState<any>({ year: String(thisYear), company_id: '' })
  const [tab, setTab] = useState('overview')
  const [period, setPeriod] = useState('all')   // 'all' | 'YYYY-MM'
  const [busy, setBusy] = useState(false)
  const [daily, setDaily] = useState<any>(null)  // {month, label, data} popup chi tiết theo ngày

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
    try {
      const [a, b] = await Promise.all([
        api.get('/api/reports/procurement', { params }),
        api.get('/api/reports/matrix', { params: { ...params, ...(refresh ? { refresh: 1 } : {}) } }),
      ])
      setD(a.data.data); setMx(b.data.data)
    } finally { setBusy(false) }
  }
  useEffect(() => {
    api.get('/api/companies', { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items))
    load()
  }, [])
  if (!d || !mx) return <div style={{ padding: 20 }}>Đang tải...</div>
  const months = mx.months || []
  const isMatrix = ['supplier', 'item_group', 'nspt', 'department', 'shipping'].includes(tab)

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
          <div><label style={{ fontSize: 12, color: 'var(--muted)' }}>Công ty</label><br />
            <select value={f.company_id} onChange={(e) => setF((s: any) => ({ ...s, company_id: e.target.value }))}>
              <option value="">Tất cả</option>{companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select></div>
          <div><label style={{ fontSize: 12, color: 'var(--muted)' }}>Năm</label><br />
            <select value={f.year} onChange={(e) => setF((s: any) => ({ ...s, year: e.target.value }))}>
              <option value="all">Tất cả</option>{[thisYear, thisYear - 1, thisYear - 2].map((y) => <option key={y} value={y}>{y}</option>)}
            </select></div>
          <button className="btn" disabled={busy} onClick={() => load(false)}>Lọc</button>
          <button className="btn secondary" disabled={busy} onClick={() => load(true)} title="Tính lại số liệu báo cáo"><i className="ti ti-refresh" />Cập nhật</button>
          <button className="btn ghost" onClick={() => window.print()}><i className="ti ti-printer" />In</button>
        </div>
      </div>

      <div className="no-print" style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 8, borderBottom: '1px solid var(--border)' }}>
        {TABS.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)} style={{ border: 'none', background: 'none', padding: '8px 12px', cursor: 'pointer', fontSize: 13.5, fontWeight: tab === t.key ? 700 : 500, color: tab === t.key ? 'var(--teal)' : 'var(--muted)', borderBottom: tab === t.key ? '2px solid var(--teal)' : '2px solid transparent' }}>{t.label}</button>
        ))}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, marginBottom: 10 }}>
        <div style={{ fontSize: 12, color: 'var(--muted)' }}>Kỳ: {f.year === 'all' ? 'Tất cả' : `Năm ${f.year}`} · {f.company_id ? companies.find((c) => String(c.id) === String(f.company_id))?.name : 'Tất cả công ty'} · Tính lúc: {mx.computed_at}</div>
        {isMatrix && (
          <div className="no-print" style={{ fontSize: 12.5 }}>Xem theo:&nbsp;
            <select value={period} onChange={(e) => setPeriod(e.target.value)}>
              <option value="all">Cả năm</option>
              {months.map((m: any) => <option key={m.key} value={m.key}>{m.label}</option>)}
            </select>
          </div>
        )}
      </div>

      {tab === 'overview' && (<>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 14 }}>
          <Card label="Số đơn mua hàng" val={fmt(d.po_count)} />
          <Card label="Giá trị đặt hàng" val={fmt(d.order_value)} color="var(--teal)" />
          <Card label="Công nợ còn phải trả" val={fmt(remaining)} sub={`Hàng ${fmt(d.payable_goods.remaining)} · VC ${fmt(d.payable_shipping.remaining)}`} />
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
            <h3 className="sec-title">Chi phí mua theo tháng <span style={{ fontSize: 11.5, fontWeight: 400, color: 'var(--muted)' }}>(rê xem số tiền · bấm cột để xem theo ngày)</span></h3>
            <BarChart data={spendSeries} color="var(--teal)" onBar={openDaily} />
          </div>
        </div>
      </>)}

      {tab === 'supplier' && <div className="card" style={{ padding: 16 }}>
        <h3 className="sec-title">Giao dịch NCC — {periodLabel} <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--muted)' }}>(đỏ = tỷ lệ trễ &gt; 30%)</span></h3>
        <ReportTable rows={mx.supplier} period={period} warnMetric="rate" nameLabel="Nhà cung cấp"
          metrics={[{ key: 'trans', label: 'Số lần giao dịch' }, { key: 'late', label: 'Số lần trễ' }, { key: 'rate', label: 'Tỷ lệ trễ', pct: true }]} />
      </div>}

      {tab === 'item_group' && <div className="card" style={{ padding: 16 }}>
        <h3 className="sec-title">Tần suất mua theo loại VTBB/NL — {periodLabel}</h3>
        <ReportTable rows={mx.item_group} period={period} nameLabel="Loại VTBB/NL"
          metrics={[{ key: 'trans', label: 'Số lần mua' }, { key: 'cost', label: 'Tổng chi phí mua' }]} />
      </div>}

      {tab === 'nspt' && <div className="card" style={{ padding: 16 }}>
        <h3 className="sec-title">Giao hàng theo NSPT — {periodLabel}</h3>
        <ReportTable rows={mx.nspt} period={period} warnMetric="rate" nameLabel="NSPT"
          metrics={[{ key: 'orders', label: 'Số đơn' }, { key: 'late', label: 'Trễ quy định' }, { key: 'ontime', label: 'Đúng hạn' }, { key: 'early', label: 'Giao sớm' }, { key: 'rate', label: 'Tỷ lệ trễ', pct: true }]} />
      </div>}

      {tab === 'department' && <div className="card" style={{ padding: 16 }}>
        <h3 className="sec-title">Đặt hàng & đơn gấp theo bộ phận — {periodLabel} <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--muted)' }}>(đỏ = tỷ lệ gấp &gt; 30%)</span></h3>
        <ReportTable rows={mx.department} period={period} warnMetric="rate" nameLabel="Bộ phận"
          metrics={[{ key: 'orders', label: 'Số lần đặt' }, { key: 'urgent', label: 'Số lần gấp' }, { key: 'rate', label: 'Tỷ lệ gấp', pct: true }]} />
      </div>}

      {tab === 'shipping' && <>
        <div className="card" style={{ padding: 16, marginBottom: 14 }}>
          <h3 className="sec-title">Chi phí vận chuyển theo đơn vị VC — {periodLabel} <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--muted)' }}>(Tỷ lệ = CP vận chuyển / Giá trị đơn hàng)</span></h3>
          <ReportTable rows={mx.shipping} period={period} nameLabel="Đơn vị vận chuyển"
            metrics={[{ key: 'freq', label: 'Tần suất' }, { key: 'order_value', label: 'Giá trị đơn hàng' }, { key: 'ship_cost', label: 'Chi phí vận chuyển' }, { key: 'rate', label: 'Tỷ lệ', pct: true }]} />
        </div>
        <div className="card" style={{ padding: 16 }}>
          <h3 className="sec-title">Chi tiết theo đơn hàng</h3>
          <div className="items-scroll">
            <table className="items-table" style={{ minWidth: 1000 }}>
              <thead><tr><th>Đơn vị VC</th><th>Tháng</th><th>Mã VTBB/NL</th><th>Mã MISA</th><th>Số HĐ</th><th>Ngày nhận</th><th style={{ textAlign: 'right' }}>SL đặt</th><th style={{ textAlign: 'right' }}>SL nhận</th><th style={{ textAlign: 'right' }}>Thành tiền ĐH</th><th style={{ textAlign: 'right' }}>Thành tiền VC</th><th style={{ textAlign: 'right' }}>Tỷ lệ</th></tr></thead>
              <tbody>
                {mx.shipping_detail.map((r: any, i: number) => (
                  <tr key={i}><td>{r.carrier}</td><td>{r.month}</td><td>{r.product_code}</td><td>{r.misa_code}</td><td>{r.invoice_no}</td><td>{r.received_date}</td>
                    <td style={{ textAlign: 'right' }}>{fmt(r.qty_order)}</td><td style={{ textAlign: 'right' }}>{fmt(r.qty_received)}</td>
                    <td style={{ textAlign: 'right' }}>{fmt(r.order_amount)}</td><td style={{ textAlign: 'right' }}>{fmt(r.ship_amount)}</td><td style={{ textAlign: 'right' }}>{pctv(r.rate)}</td></tr>))}
                {mx.shipping_detail.length === 0 && <tr><td colSpan={11} style={{ textAlign: 'center', color: '#999', padding: 14 }}>Chưa có chi phí vận chuyển</td></tr>}
              </tbody>
            </table>
          </div>
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
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.45)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }} onClick={() => setDaily(null)}>
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
