import { useState, type CSSProperties } from 'react'
import { api } from '../api/client'
import DateRangePicker from './DateRangePicker'
import SearchSelect from './SearchSelect'
import { ReportTable, fmt, pctv, type Metric } from './report-table'

// Tab báo cáo ma trận (đối tượng × tháng) dùng chung cho NSPT & Bộ phận.
// 3 chế độ: lọc khoảng ngày (1 bảng phẳng) · Ngang (pivot 12 tháng + cột Tổng cả năm) · Dọc (khối Tổng + 12 khối tháng).
// Dữ liệu năm-tháng có sẵn trong rows (r.m[YYYY-MM] + r[chỉ số] = tổng cả năm). Khoảng ngày gọi rangeEndpoint tính realtime.

// Nền xen kẽ theo cụm tháng cho dễ phân biệt (header đậm hơn body)
const MONTH_HEAD = ['#e0edfb', '#e7f6ec', '#fdf1dc', '#f3e8fb', '#fde4e4', '#ddf3f6']
const MONTH_BODY = ['#f4f9ff', '#f1faf4', '#fefaf0', '#faf5fe', '#fef3f3', '#f0fafc']
const TOTAL_HEAD = '#dbe2ea', TOTAL_BODY = '#eef2f7'   // nhóm Tổng cả năm — xám nổi bật

const thisYear = new Date().getFullYear()

export default function MatrixPivotTab({
  rows, months, metrics, nameLabel, title, warnHint = '', yearLabel, rangeEndpoint, companyId, nameWidth = 150, nameFilter = false,
}: {
  rows: any[]
  months: any[]
  metrics: Metric[]
  nameLabel: string
  title: string
  warnHint?: string
  yearLabel: string
  rangeEndpoint: string
  companyId: any
  nameWidth?: number   // độ rộng tối thiểu cột tên (NCC dài → cần rộng hơn)
  nameFilter?: boolean // hiện dropdown lọc theo 1 đối tượng (vd chọn 1 NCC)
}) {
  const [view, setView] = useState<'ngang' | 'doc'>('ngang')
  const [range, setRange] = useState({ from: '', to: '' })
  const [data, setData] = useState<any[] | null>(null)   // kết quả lọc khoảng ngày (null = xem 12 tháng)
  const [busy, setBusy] = useState(false)
  const [pick, setPick] = useState('')   // lọc theo 1 đối tượng (key), '' = tất cả

  // Nguồn options + rows sau lọc theo đối tượng đã chọn
  const baseRows: any[] = data !== null ? data : rows
  const pickOptions = Array.from(new Set(baseRows.map((r) => r.key).filter(Boolean))).sort()
  const shownRows = pick ? baseRows.filter((r) => r.key === pick) : baseRows

  async function loadRange(v: { from: string; to: string }) {
    if (!v.from || !v.to || v.from > v.to) return
    setRange(v)
    setBusy(true)
    const params: any = { date_from: v.from, date_to: v.to }
    if (companyId) params.company_id = companyId
    try {
      const r = await api.get(rangeEndpoint, { params })
      setData(r.data.data)
    } finally { setBusy(false) }
  }
  function clearRange() { setRange({ from: '', to: '' }); setData(null) }

  // Nhãn kỳ cho bản in: khoảng ngày (nếu đang lọc) hoặc cả năm
  const dlbl = (s: string) => s ? `${s.slice(8, 10)}/${s.slice(5, 7)}/${s.slice(0, 4)}` : ''
  const printLabel = data !== null ? `${dlbl(range.from)} → ${dlbl(range.to)}` : yearLabel

  return (
    <>
      {/* ==== Thanh điều khiển ==== */}
      <div className="no-print" style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
        {data === null && (
          <div style={{ display: 'inline-flex', border: '1px solid var(--border)', borderRadius: 10, overflow: 'hidden' }}>
            {([['ngang', 'ti-layout-columns', 'Ngang'], ['doc', 'ti-layout-rows', 'Dọc']] as const).map(([v, ic, lb]) => (
              <button key={v} onClick={() => setView(v)} title={`Hiển thị ${lb.toLowerCase()}`}
                style={{ display: 'inline-flex', alignItems: 'center', gap: 5, border: 'none', padding: '0 12px', height: 40, cursor: 'pointer', fontSize: 13, fontWeight: view === v ? 700 : 500, background: view === v ? 'var(--teal)' : '#fff', color: view === v ? '#fff' : 'var(--muted)' }}>
                <i className={`ti ${ic}`} />{lb}
              </button>
            ))}
          </div>
        )}
        {/* Nhóm lọc + chọn ngày đẩy sang phải */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginLeft: 'auto' }}>
          {nameFilter && (
            <div style={{ minWidth: 240 }}>
              <SearchSelect value={pick} placeholder={`Tất cả ${nameLabel.toLowerCase()}`}
                options={[{ value: '', label: `Tất cả ${nameLabel.toLowerCase()}` }, ...pickOptions.map((k) => ({ value: k, label: k }))]}
                onChange={(v) => setPick(v)} />
            </div>
          )}
          <DateRangePicker value={range} onChange={setRange} onApply={loadRange} startYear={thisYear - 5} endYear={thisYear + 1} />
          {busy && <span style={{ fontSize: 12.5, color: 'var(--muted)' }}><i className="ti ti-loader-2" /> Đang xem…</span>}
          {data !== null && !busy && <button className="btn ghost" onClick={clearRange} title="Về xem cả năm theo tháng"><i className="ti ti-x" />Xóa lọc</button>}
        </div>
      </div>

      {/* Trên màn hình: pivot Ngang/Dọc/khoảng ngày */}
      <div className="screen-only">
        {renderBody({ view, data: data !== null ? shownRows : null, range, rows: data !== null ? rows : shownRows, months, metrics, nameLabel, title, warnHint, yearLabel, nameWidth })}
      </div>
      {/* Khi IN: bản tổng hợp cả năm gọn (mỗi đối tượng 1 dòng = tổng cả năm / tổng khoảng ngày) */}
      <div className="print-only card" style={{ padding: 16 }}>
        <h3 className="sec-title">{title} — {printLabel} <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--muted)' }}>(bản tổng hợp)</span></h3>
        <ReportTable rows={shownRows} period="all" warnMetric="rate" nameLabel={nameLabel} metrics={metrics} nameMinWidth={nameWidth} />
      </div>
    </>
  )
}

function renderBody({ view, data, range, rows, months, metrics, nameLabel, title, warnHint, yearLabel, nameWidth }: any) {
  // ==== Chế độ lọc khoảng ngày → 1 bảng phẳng ====
  if (data !== null) {
    const dlbl = (s: string) => s ? `${s.slice(8, 10)}/${s.slice(5, 7)}/${s.slice(0, 4)}` : ''
    return (
      <div className="card" style={{ padding: 16 }}>
        <h3 className="sec-title">{title} — {dlbl(range.from)} → {dlbl(range.to)}</h3>
        <ReportTable rows={data} period="all" warnMetric="rate" nameLabel={nameLabel} metrics={metrics} nameMinWidth={nameWidth} />
      </div>
    )
  }

  // ==== View DỌC: khối Tổng cả năm + 12 khối tháng xếp chồng ====
  if (view === 'doc') {
    return (
      <div className="card" style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 18 }}>
        <div>
          <h3 className="sec-title" style={{ color: 'var(--teal)' }}><i className="ti ti-sigma" style={{ marginRight: 6 }} />Tổng cả năm — {yearLabel}{warnHint && <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--muted)' }}> ({warnHint})</span>}</h3>
          <ReportTable rows={rows} period="all" warnMetric="rate" nameLabel={nameLabel} metrics={metrics} nameMinWidth={nameWidth} />
        </div>
        {months.map((mo: any) => (
          <div key={mo.key}>
            <h3 className="sec-title">Tháng {mo.label}</h3>
            <ReportTable rows={rows.filter((r: any) => r.m?.[mo.key])} period={mo.key} warnMetric="rate" nameLabel={nameLabel} metrics={metrics} nameMinWidth={nameWidth} />
          </div>
        ))}
        {months.length === 0 && <div style={{ color: '#999', textAlign: 'center', padding: 14 }}>Không có dữ liệu</div>}
      </div>
    )
  }

  // ==== View NGANG: pivot đối tượng (dọc) × tháng (ngang) + nhóm cột Tổng cả năm ====
  const stickyTh: CSSProperties = { position: 'sticky', left: 0, zIndex: 3, background: '#f1f5f9' }
  const stickyTd: CSSProperties = { position: 'sticky', left: 0, zIndex: 1, background: '#fff', textAlign: 'left', fontWeight: 500 }
  return (
    <div className="card" style={{ padding: 16 }}>
      <h3 className="sec-title">{title} — {yearLabel} <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--muted)' }}>(phân cụm theo tháng · cuộn ngang · cột xám = tổng cả năm{warnHint ? ` · ${warnHint}` : ''})</span></h3>
      <div className="items-scroll">
        <table className="items-table" style={{ minWidth: 520 }}>
          <thead>
            <tr>
              <th rowSpan={2} style={{ ...stickyTh, textAlign: 'left', minWidth: nameWidth, verticalAlign: 'bottom' }}>{nameLabel}</th>
              {months.map((mo: any, ci: number) => (
                <th key={mo.key} colSpan={metrics.length} style={{ textAlign: 'center', borderLeft: '2px solid var(--border)', background: MONTH_HEAD[ci % MONTH_HEAD.length] }}>Tháng {mo.label}</th>
              ))}
              <th colSpan={metrics.length} style={{ textAlign: 'center', borderLeft: '3px solid #94a3b8', background: TOTAL_HEAD, color: 'var(--navy)' }}>Tổng cả năm</th>
            </tr>
            <tr>
              {months.map((mo: any, ci: number) => metrics.map((m: Metric, mi: number) => (
                <th key={mo.key + m.key} style={{ textAlign: 'right', fontWeight: 500, fontSize: 11.5, borderLeft: mi === 0 ? '2px solid var(--border)' : undefined, background: MONTH_HEAD[ci % MONTH_HEAD.length] }}>{m.label}</th>
              )))}
              {metrics.map((m: Metric, mi: number) => (
                <th key={'tot' + m.key} style={{ textAlign: 'right', fontWeight: 700, fontSize: 11.5, borderLeft: mi === 0 ? '3px solid #94a3b8' : undefined, background: TOTAL_HEAD }}>{m.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r: any, i: number) => {
              const twarn = Number(r.rate) > 30
              return (
                <tr key={i}>
                  <td style={stickyTd}>{r.key}</td>
                  {months.map((mo: any, ci: number) => {
                    const c = r.m?.[mo.key]
                    const warn = c && Number(c.rate) > 30
                    return metrics.map((m: Metric, mi: number) => {
                      const v = c ? (c[m.key] ?? 0) : 0
                      const isRate = m.key === 'rate'
                      return (
                        <td key={mo.key + m.key} style={{ textAlign: 'right', borderLeft: mi === 0 ? '2px solid var(--border)' : undefined, background: MONTH_BODY[ci % MONTH_BODY.length], color: isRate && warn ? 'var(--red)' : (c ? 'inherit' : '#cbd5e1'), fontWeight: isRate && warn ? 600 : 400 }}>
                          {m.pct ? pctv(v) : fmt(v)}
                        </td>
                      )
                    })
                  })}
                  {metrics.map((m: Metric, mi: number) => {
                    const isRate = m.key === 'rate'
                    return (
                      <td key={'tot' + m.key} style={{ textAlign: 'right', borderLeft: mi === 0 ? '3px solid #94a3b8' : undefined, background: TOTAL_BODY, fontWeight: 700, color: isRate && twarn ? 'var(--red)' : 'var(--navy)' }}>
                        {m.pct ? pctv(r[m.key] ?? 0) : fmt(r[m.key] ?? 0)}
                      </td>
                    )
                  })}
                </tr>
              )
            })}
            {(rows.length === 0 || months.length === 0) && <tr><td colSpan={1 + (months.length + 1) * metrics.length} style={{ textAlign: 'center', color: '#999', padding: 14 }}>Không có dữ liệu</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
