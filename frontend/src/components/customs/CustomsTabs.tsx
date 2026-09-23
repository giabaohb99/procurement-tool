// bao-CR-470 — ba thẻ phụ của màn Tra cứu giá hải quan: Nhà nhập khẩu (T-05), So sánh (B-05),
// Pháp lý & thuế (P-03 · P-04). Cả ba chỉ chạy khi đã có từ khóa hoặc mã HS, trừ ô tra cứu
// hóa chất của thẻ Pháp lý (tra độc lập theo tên / CAS / công thức).
import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import {
  CustomsFilters, fmtDate, fmtQty, fmtTick, fmtUsd, niceScale, PERIODS, toParams, unitChip, unitLabel, useWidth,
} from './customs-shared'

const UnitChips = ({ units, unit, onPick }: { units: any[]; unit: string; onPick: (u: string) => void }) => (
  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center', marginBottom: 10, fontSize: 13 }}>
    <span style={{ color: 'var(--muted)' }}>Đơn vị:</span>
    {units.map((x) => (
      <button key={x.unit} className={x.unit === unit ? 'btn' : 'btn ghost'} style={{ padding: '3px 10px' }}
        onClick={() => onPick(x.unit)}>{unitChip(x.unit)} · {x.count} dòng</button>
    ))}
  </div>
)

// ── Nhà nhập khẩu ─────────────────────────────────────────────────────────
export function CustomsImporters({ filters, onPickImporter }: {
  filters: CustomsFilters
  onPickImporter: (id: number, name: string) => void
}) {
  const [unit, setUnit] = useState('')
  const [data, setData] = useState<any>(null)
  useEffect(() => {
    let alive = true   // chỉ nhận phản hồi của lượt gọi mới nhất
    api.get('/api/customs/importers', { params: { ...toParams({ ...filters, importer_id: '' }), chart_unit: unit } })
      .then((r) => { if (alive) setData(r.data.data) }).catch(() => { if (alive) setData(null) })
    return () => { alive = false }
  }, [filters, unit])
  if (!data) return <div className="card" style={{ padding: 16, color: 'var(--muted)' }}>Đang tải…</div>
  const u = unitLabel(data.unit)
  return (
    <div>
      <UnitChips units={data.units} unit={data.unit} onPick={setUnit} />
      <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 8 }}>
        {data.total_importers} doanh nghiệp nhập hàng khớp bộ lọc (đơn vị {data.unit}); hiện 20 doanh nghiệp nhập nhiều nhất.
        Gộp theo MÃ SỐ THUẾ. Bấm một dòng để lọc danh sách và biểu đồ theo doanh nghiệp đó.
      </div>
      <div className="card table-card"><div className="table-scroll"><table>
        <thead><tr>
          <th style={{ width: 40 }}>#</th><th>Doanh nghiệp</th><th>Mã số thuế</th><th style={{ textAlign: 'right' }}>Số dòng</th>
          <th style={{ textAlign: 'right' }}>Tổng lượng ({u})</th><th style={{ textAlign: 'right' }}>Thị phần</th>
          <th style={{ textAlign: 'right' }}>Giá BQ (USD/{u})</th><th>Lần nhập gần nhất</th>
        </tr></thead>
        <tbody>
          {data.items.map((x: any, i: number) => (
            <tr key={x.importer_id} className="clickable" onClick={() => onPickImporter(x.importer_id, x.name)}>
              <td>{i + 1}</td>
              <td>{x.name}</td>
              <td>{x.tax_code}</td>
              <td style={{ textAlign: 'right' }}>{x.count}</td>
              <td style={{ textAlign: 'right' }}>{fmtQty(x.qty)}</td>
              <td style={{ textAlign: 'right' }}>
                {x.share == null ? '—' : (
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ width: 60, height: 6, background: '#e5e7eb', borderRadius: 3, overflow: 'hidden' }}>
                      <span style={{ display: 'block', height: 6, width: `${Math.round(x.share * 100)}%`, background: 'var(--teal)' }} />
                    </span>
                    {(x.share * 100).toFixed(1)}%
                  </span>
                )}
              </td>
              <td style={{ textAlign: 'right' }}>{fmtUsd(x.wavg)}</td>
              <td>{fmtDate(x.last_date)}</td>
            </tr>
          ))}
          {!data.items.length && <tr><td colSpan={8} className="table-empty">Không có doanh nghiệp nào khớp bộ lọc</td></tr>}
        </tbody>
      </table></div></div>
    </div>
  )
}

// ── So sánh nhiều mặt hàng ────────────────────────────────────────────────
const COLORS = ['#00aeef', '#f97316', '#16a34a', '#a855f7', '#e11d48']

export function CustomsCompare({ filters }: { filters: CustomsFilters }) {
  const [terms, setTerms] = useState<string[]>(() => (filters.q.trim() ? [filters.q.trim(), ''] : ['', '']))
  const [period, setPeriod] = useState('month')
  const [unit, setUnit] = useState('')
  const [data, setData] = useState<any>(null)
  const [err, setErr] = useState('')

  async function run(nextUnit = unit) {
    const list = terms.map((t) => t.trim()).filter(Boolean)
    if (list.length < 2) { setErr('Nhập ít nhất 2 mặt hàng / hoạt chất để so sánh.'); return }
    setErr('')
    const params = new URLSearchParams()
    Object.entries({ ...toParams({ ...filters, q: '' }), period, chart_unit: nextUnit })
      .forEach(([k, v]) => v && params.append(k, String(v)))
    list.forEach((t) => params.append('terms', t))
    try {
      const r = await api.get(`/api/customs/compare?${params.toString()}`, { _silent: true } as any)
      setData(r.data.data)
    } catch (e: any) { setErr(e?.response?.data?.error?.message || 'Không so sánh được') }
  }

  const periods: string[] = data ? Array.from(new Set<string>(data.terms.flatMap((t: any) => t.series.map((s: any) => s.period)))).sort() : []
  const labelOf = (p: string) => data?.terms.flatMap((t: any) => t.series).find((s: any) => s.period === p)?.label || p
  return (
    <div>
      <div className="card" style={{ padding: 12, marginBottom: 12 }}>
        <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 8 }}>
          So sánh giá bình quân gia quyền của 2–5 mặt hàng / hoạt chất trên CÙNG một đơn vị tính.
          Bộ lọc khác (mã HS, xuất xứ, khoảng ngày…) áp chung cho mọi mặt hàng.
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          {terms.map((t, i) => (
            <span key={i} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 10, height: 10, borderRadius: 10, background: COLORS[i] }} />
              <input value={t} placeholder={`Mặt hàng ${i + 1}`} style={{ width: 170 }}
                onChange={(e) => setTerms((xs) => xs.map((x, j) => (j === i ? e.target.value : x)))}
                onKeyDown={(e) => e.key === 'Enter' && run()} />
              {terms.length > 2 && (
                <button className="btn ghost" title="Bỏ" onClick={() => setTerms((xs) => xs.filter((_, j) => j !== i))}>
                  <i className="ti ti-x" />
                </button>
              )}
            </span>
          ))}
          {terms.length < 5 && <button className="btn ghost" onClick={() => setTerms((xs) => [...xs, ''])}><i className="ti ti-plus" />Thêm</button>}
          <select value={period} onChange={(e) => setPeriod(e.target.value)}>
            {PERIODS.map((p) => <option key={p.value} value={p.value}>Theo {p.label.toLowerCase()}</option>)}
          </select>
          <button className="btn" onClick={() => { setUnit(''); run('') }}><i className="ti ti-arrows-diff" />So sánh</button>
        </div>
        {err && <div style={{ color: '#b91c1c', fontSize: 13, marginTop: 8 }}>{err}</div>}
      </div>

      {data && (
        <>
          <UnitChips units={data.units} unit={data.unit} onPick={(u) => { setUnit(u); run(u) }} />
          <CompareSvg data={data} periods={periods} labelOf={labelOf} />
          <div className="card table-card" style={{ marginTop: 12 }}><div className="table-scroll"><table>
            <thead><tr>
              <th>Kỳ</th>
              {data.terms.map((t: any, i: number) => (
                <th key={t.term} style={{ textAlign: 'right', color: COLORS[i] }}>{t.term} (USD/{unitLabel(data.unit)})</th>
              ))}
            </tr></thead>
            <tbody>
              {periods.map((p) => (
                <tr key={p}>
                  <td>{labelOf(p)}</td>
                  {data.terms.map((t: any) => {
                    const s = t.series.find((x: any) => x.period === p)
                    return (
                      <td key={t.term} style={{ textAlign: 'right' }}>
                        {s && s.wavg != null ? <>{fmtUsd(s.wavg)} <span style={{ color: 'var(--muted)', fontSize: 11 }}>({s.count})</span></> : '—'}
                      </td>
                    )
                  })}
                </tr>
              ))}
              <tr style={{ fontWeight: 600 }}>
                <td>Cả khoảng</td>
                {data.terms.map((t: any) => (
                  <td key={t.term} style={{ textAlign: 'right' }}>{fmtUsd(t.kpi?.wavg)} <span style={{ color: 'var(--muted)', fontSize: 11 }}>({t.kpi?.count ?? 0})</span></td>
                ))}
              </tr>
            </tbody>
          </table></div></div>
          <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 6 }}>Số trong ngoặc là số dòng hàng của kỳ đó.</div>
        </>
      )}
    </div>
  )
}

function CompareSvg({ data, periods, labelOf }: { data: any; periods: string[]; labelOf: (p: string) => string }) {
  // Vẽ đúng bề rộng đo được (không co giãn viewBox — chữ trục phình theo màn hình), mỗi kỳ một ô,
  // rê chuột một kỳ thì hiện giá của mọi mặt hàng ở kỳ đó.
  const { ref, width } = useWidth()
  const [hover, setHover] = useState<number | null>(null)
  const H = 260, L = 64, R = 16, T = 12, B = 28
  const at = (t: any, p: string) => t.series.find((s: any) => s.period === p)
  const vals = data.terms.flatMap((t: any) => t.series.map((s: any) => s.wavg)).filter((v: any) => v != null) as number[]
  if (!vals.length || !periods.length) return <div className="card" style={{ padding: 16, color: 'var(--muted)' }}>Không có giá để vẽ ở đơn vị này.</div>
  const sc = niceScale(Math.min(...vals) * 0.95, Math.max(...vals) * 1.05)
  const n = periods.length
  const slot = Math.max(width - L - R, 1) / n
  const x = (i: number) => L + slot * (i + 0.5)
  const y = (v: number) => T + (H - T - B) * (1 - (v - sc.min) / (sc.max - sc.min || 1))
  const labelEvery = Math.max(1, Math.ceil(64 / slot))
  const tipLeft = hover != null ? (x(hover) > width / 2 ? x(hover) - 12 - 260 : x(hover) + 12) : 0
  return (
    <div className="card" style={{ padding: 12 }}>
      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', fontSize: 12, marginBottom: 6 }}>
        {data.terms.map((t: any, i: number) => (
          <span key={t.term} style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
            <span style={{ width: 14, height: 3, background: COLORS[i] }} />{t.term}
          </span>
        ))}
        <span style={{ color: 'var(--muted)' }}>· Rê chuột lên biểu đồ để xem số từng kỳ</span>
      </div>
      <div ref={ref} style={{ position: 'relative' }} onMouseLeave={() => setHover(null)}>
        {width > 0 && (
          <svg width={width} height={H} style={{ display: 'block' }} role="img" aria-label="So sánh giá theo kỳ">
            {sc.ticks.map((v) => (
              <g key={v}>
                <line x1={L} x2={width - R} y1={y(v)} y2={y(v)} stroke="#eef2f6" />
                <text x={L - 8} y={y(v) + 4} textAnchor="end" fontSize="11" fill="#64748b">{fmtTick(v)}</text>
              </g>
            ))}
            <text x={4} y={T + 4} fontSize="10.5" fill="#94a3b8">USD/{unitLabel(data.unit)}</text>
            {hover != null && <line x1={x(hover)} x2={x(hover)} y1={T} y2={H - B} stroke="#94a3b8" strokeDasharray="3 3" />}
            {data.terms.map((t: any, ti: number) => {
              const pts = periods.map((p, i) => ({ i, s: at(t, p) }))
              // Kỳ trống cắt đường, không nối qua
              const segs: { i: number; v: number }[][] = []
              let cur: { i: number; v: number }[] = []
              for (const p of pts) {
                if (p.s && p.s.wavg != null) cur.push({ i: p.i, v: p.s.wavg })
                else if (cur.length) { segs.push(cur); cur = [] }
              }
              if (cur.length) segs.push(cur)
              return (
                <g key={t.term} pointerEvents="none">
                  {segs.map((sg, k) => (
                    <polyline key={k} fill="none" stroke={COLORS[ti]} strokeWidth="2"
                      points={sg.map((p) => `${x(p.i)},${y(p.v)}`).join(' ')} />
                  ))}
                  {pts.filter((p) => p.s && p.s.wavg != null).map((p) => (
                    <circle key={p.i} cx={x(p.i)} cy={y(p.s.wavg)} r={p.i === hover ? 5 : 3.5} stroke={COLORS[ti]} strokeWidth="2"
                      fill={p.s.low_data ? '#fff' : COLORS[ti]} />
                  ))}
                </g>
              )
            })}
            {periods.map((p, i) => (i % labelEvery === 0 || i === n - 1) && (
              <text key={p} x={x(i)} y={H - 8} textAnchor="middle" fontSize="11" fill={i === hover ? '#0f172a' : '#64748b'}>{labelOf(p)}</text>
            ))}
            {periods.map((p, i) => (
              <rect key={`h${p}`} x={L + slot * i} y={0} width={slot} height={H} fill="transparent" onMouseEnter={() => setHover(i)} />
            ))}
          </svg>
        )}
        {hover != null && (
          <div style={{ position: 'absolute', top: 8, left: Math.max(0, tipLeft), width: 260, pointerEvents: 'none',
            background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, boxShadow: '0 8px 24px rgba(15,23,42,.12)',
            padding: '8px 12px', fontSize: 12.5, zIndex: 2 }}>
            <div style={{ fontWeight: 700, marginBottom: 4 }}>{labelOf(periods[hover])}</div>
            {data.terms.map((t: any, i: number) => {
              const s = at(t, periods[hover])
              return (
                <div key={t.term} style={{ display: 'flex', gap: 6, alignItems: 'center', padding: '1px 0' }}>
                  <span style={{ width: 8, height: 8, borderRadius: 8, background: COLORS[i], flexShrink: 0 }} />
                  <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.term}</span>
                  <b>{s && s.wavg != null ? fmtUsd(s.wavg) : '—'}</b>
                  <span style={{ color: 'var(--muted)', fontSize: 11 }}>({s?.count ?? 0} dòng)</span>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Pháp lý & thuế ────────────────────────────────────────────────────────
export function CustomsLegal({ filters, alerts }: { filters: CustomsFilters; alerts: any[] }) {
  const [term, setTerm] = useState(filters.q)
  const [reg, setReg] = useState<any>(null)
  const [regErr, setRegErr] = useState('')
  const [hs, setHs] = useState(filters.hs_code)
  const [tariff, setTariff] = useState<any[] | null>(null)
  const [tariffErr, setTariffErr] = useState('')

  async function lookupReg(t = term) {
    if (t.trim().length < 2) { setRegErr('Nhập ít nhất 2 ký tự: tên hóa chất, số CAS hoặc công thức'); return }
    setRegErr('')
    try {
      const r = await api.get('/api/customs/regulations/lookup', { params: { q: t.trim() }, _silent: true } as any)
      setReg(r.data.data)
    } catch (e: any) { setRegErr(e?.response?.data?.error?.message || 'Không tra được') }
  }
  async function lookupTariff(code = hs) {
    if (code.replace(/\D/g, '').length < 4) { setTariffErr('Mã HS phải có ít nhất 4 chữ số'); return }
    setTariffErr('')
    try {
      const r = await api.get('/api/customs/tariff', { params: { hs_code: code }, _silent: true } as any)
      setTariff(r.data.data)
    } catch (e: any) { setTariffErr(e?.response?.data?.error?.message || 'Không tra được') }
  }
  useEffect(() => {
    setTerm(filters.q); setHs(filters.hs_code)
    if (filters.q.trim().length >= 2) lookupReg(filters.q)
    if (filters.hs_code.replace(/\D/g, '').length >= 4) lookupTariff(filters.hs_code)
  }, [filters.q, filters.hs_code]) // chạy lại khi đổi từ khóa / mã HS ở thanh lọc

  return (
    <div style={{ display: 'grid', gap: 12 }}>
      <div style={{ fontSize: 12, color: 'var(--muted)' }}>
        Tra cứu tham khảo từ văn bản đã nạp (NĐ 24/2026/NĐ-CP · TT 75/2025/TT-BNNMT · TT 01/2026/TT-BCT · biểu thuế 2026).
        Không thay cho ý kiến pháp chế — đối chiếu văn bản gốc trước khi quyết định.
      </div>
      {alerts.length > 0 && (
        <div className="card" style={{ padding: 12 }}>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Cảnh báo cho từ khóa «{filters.q}»</div>
          <RegTable items={alerts} />
        </div>
      )}

      <div className="card" style={{ padding: 12 }}>
        <div style={{ fontWeight: 600, marginBottom: 8 }}>Tra hóa chất trong danh mục pháp lý</div>
        <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
          <input value={term} onChange={(e) => setTerm(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && lookupReg()}
            placeholder="Tên, số CAS hoặc công thức (vd H2SO4, 7664-93-9, Ammonia)" style={{ flex: 1 }} />
          <button className="btn" onClick={() => lookupReg()}><i className="ti ti-search" />Tra</button>
        </div>
        {regErr && <div style={{ color: '#b91c1c', fontSize: 13 }}>{regErr}</div>}
        {reg && (
          <>
            {reg.formula_cas && <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 6 }}>Công thức {reg.term} → CAS {reg.formula_cas}</div>}
            {reg.items.length ? <RegTable items={reg.items} /> : <div style={{ fontSize: 13, color: 'var(--muted)' }}>Không có trong danh mục nào đã nạp.</div>}
          </>
        )}
      </div>

      <div className="card" style={{ padding: 12 }}>
        <div style={{ fontWeight: 600, marginBottom: 8 }}>Biểu thuế nhập khẩu theo mã HS</div>
        <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
          <input value={hs} onChange={(e) => setHs(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && lookupTariff()}
            placeholder="Mã HS, vd 38089199" style={{ width: 220 }} />
          <button className="btn" onClick={() => lookupTariff()}><i className="ti ti-search" />Tra</button>
        </div>
        {tariffErr && <div style={{ color: '#b91c1c', fontSize: 13 }}>{tariffErr}</div>}
        {tariff && (tariff.length ? <TariffTable rows={tariff} /> : <div style={{ fontSize: 13, color: 'var(--muted)' }}>Không có mã này trong biểu thuế đã nạp.</div>)}
      </div>
    </div>
  )
}

function RegTable({ items }: { items: any[] }) {
  return (
    <div className="table-scroll"><table>
      <thead><tr><th>Danh mục</th><th>Tên</th><th>Số CAS</th><th>Lưu ý</th></tr></thead>
      <tbody>
        {items.map((r) => (
          <tr key={r.id}>
            <td style={{ whiteSpace: 'nowrap' }}>
              <span className={`badge ${r.list_code === 10 ? 'err' : r.list_code === 4 ? 'warn' : 'info'}`}>{r.list_label}</span>
            </td>
            <td>{r.name}{r.name_vi && r.name_vi !== r.name ? <div style={{ fontSize: 12, color: 'var(--muted)' }}>{r.name_vi}</div> : null}</td>
            <td>{r.cas_no || '—'}</td>
            <td style={{ fontSize: 13 }}>{r.obligation}</td>
          </tr>
        ))}
      </tbody>
    </table></div>
  )
}

const rate = (v: any) => (v == null || v === '' ? '—' : `${v}`)

function TariffTable({ rows }: { rows: any[] }) {
  const leaf = rows.filter((r) => r.hs_code.length >= 8)
  const ftaKeys = Array.from(new Set(leaf.flatMap((r) => Object.keys(r.fta || {})))).sort()
  return (
    <>
      <div className="table-scroll"><table>
        <thead><tr>
          <th>Mã HS</th><th>Mô tả</th><th>ĐVT</th><th style={{ textAlign: 'right' }}>Thông thường</th>
          <th style={{ textAlign: 'right' }}>Ưu đãi (MFN)</th><th style={{ textAlign: 'right' }}>VAT</th><th>Chính sách</th>
        </tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.hs_code} style={r.hs_code.length < 8 ? { color: 'var(--muted)' } : undefined}>
              <td style={{ fontWeight: r.hs_code.length >= 8 ? 600 : 400 }}>{r.hs_code}</td>
              <td>{r.name_vn}</td>
              <td>{r.unit || ''}</td>
              <td style={{ textAlign: 'right' }}>{rate(r.rate_normal)}</td>
              <td style={{ textAlign: 'right' }}>{rate(r.rate_mfn)}</td>
              <td style={{ textAlign: 'right' }}>{rate(r.rate_vat)}</td>
              <td style={{ fontSize: 12 }}>{r.policy || ''}</td>
            </tr>
          ))}
        </tbody>
      </table></div>
      {ftaKeys.length > 0 && (
        <>
          <div style={{ fontSize: 13, fontWeight: 600, margin: '10px 0 6px' }}>Thuế suất theo hiệp định thương mại tự do (%)</div>
          <div className="table-scroll"><table>
            <thead><tr><th>Mã HS</th>{ftaKeys.map((k) => <th key={k} style={{ textAlign: 'right' }}>{k}</th>)}</tr></thead>
            <tbody>
              {leaf.map((r) => (
                <tr key={r.hs_code}>
                  <td>{r.hs_code}</td>
                  {ftaKeys.map((k) => <td key={k} style={{ textAlign: 'right' }}>{rate(r.fta?.[k])}</td>)}
                </tr>
              ))}
            </tbody>
          </table></div>
        </>
      )}
    </>
  )
}
