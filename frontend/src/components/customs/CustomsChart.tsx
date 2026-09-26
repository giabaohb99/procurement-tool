// bao-CR-470 — thẻ «Biểu đồ» của màn Tra cứu giá hải quan (bản cũ).
//
// Bản cũ KHÔNG có thư viện biểu đồ — vẽ SVG tay (không sửa pages/Reports.tsx, không thêm thư
// viện). Bốn luật lấy từ số liệu thật của ATRAZINE (04-giao-dien.md §4), đừng "làm cho đẹp" mà bỏ:
//   1. Tách theo đơn vị — kg và lít không vẽ chung.
//   2. Kỳ không có dòng nào để TRỐNG: không vẽ 0, không nối đường qua.
//   3. Kỳ dưới `min_lines_for_best` dòng vẽ điểm RỖNG và không được gắn nhãn "tốt nhất".
//   4. Dải tô nhạt là KHOẢNG GIÁ PHỔ BIẾN (phân vị 25–75%), KHÔNG phải thấp–cao: vài dòng giá
//      lạ (gói nhỏ, khai sai đơn vị — đo được 250 USD/lít giữa đám 2–4 USD/lít) kéo trục lên
//      trần và ép đường giá dẹp sát đáy. Thấp / cao vẫn hiện ở ô rê chuột và bảng.
//
// SVG vẽ theo ĐÚNG bề rộng đo được của khung (ResizeObserver), không co giãn bằng viewBox —
// co giãn viewBox làm chữ trên trục phình theo bề ngang màn hình. Hai biểu đồ giá và lượng
// dùng CHUNG một trục ngang (mỗi kỳ một ô), nên nhãn tháng thẳng hàng và rê chuột một chỗ là
// cả hai cùng sáng.
import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import {
  CustomsFilters, fmtCompact, fmtDate, fmtQty, fmtTick, fmtUsd, niceScale, PERIODS, toParams, unitChip, unitLabel, useWidth,
} from './customs-shared'

const PAD_L = 64, PAD_R = 16
const PRICE_H = 280, PRICE_T = 12, PRICE_B = 28
const QTY_H = 150, QTY_T = 18, QTY_B = 26
const BAND = 'rgba(0,174,239,.16)'
const GREEN = '#16a34a'

export default function CustomsChart({ filters }: { filters: CustomsFilters }) {
  const [period, setPeriod] = useState('month')
  // bao-CR-493: đại ca chốt bỏ hẳn nút chọn giá — biểu đồ luôn vẽ GIÁ ĐIỀU CHỈNH (giá hải quan áp
  // lại để tính thuế); ai cần giá khai báo thì thẻ Danh sách vẫn có đủ hai cột.
  const priceMode = 'adjusted'
  const [chartUnit, setChartUnit] = useState('')
  const [data, setData] = useState<any>(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    // Bấm đổi kỳ / đơn vị liền tay là nhiều lượt gọi chồng nhau —
    // chỉ nhận phản hồi của lượt MỚI NHẤT, kẻo phản hồi cũ về sau đè lên số mới.
    let alive = true
    setErr('')
    api.get('/api/customs/stats', {
      params: { ...toParams(filters), period, price_mode: priceMode, chart_unit: chartUnit }, _silent: true,
    } as any)
      .then((r) => { if (alive) setData(r.data.data) })
      .catch((e) => { if (alive) { setData(null); setErr(e?.response?.data?.error?.message || 'Không tải được biểu đồ') } })
    return () => { alive = false }
  }, [filters, period, priceMode, chartUnit])

  if (err) return <div className="card" style={{ padding: 16, color: 'var(--muted)' }}>{err}</div>
  if (!data) return <div className="card" style={{ padding: 16, color: 'var(--muted)' }}>Đang tính…</div>

  const { kpi, series, units, unit, coverage, best_period: best, min_lines_for_best: minLines } = data
  if (!kpi?.count) return (
    <div className="card" style={{ padding: 16, color: 'var(--muted)' }}>
      Không có dòng hàng nào khớp bộ lọc — thử bỏ bớt điều kiện hoặc đổi từ khóa.
    </div>
  )
  const u = unitLabel(unit)
  const years = coverage.years
  return (
    <div>
      {/* bao-CR-493: Kỳ và Đơn vị nằm chung MỘT thẻ (đề xuất đại ca 25/09) — đều là cách cắt cùng một biểu đồ. */}
      <div className="card" style={{ padding: '10px 14px', marginBottom: 12, fontSize: 13, display: 'flex',
        flexDirection: 'column', gap: 8 }}>
        <Seg label="Kỳ" value={period} onChange={setPeriod} options={PERIODS} />
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ color: 'var(--muted)' }}>Đơn vị (vẽ từng đơn vị một):</span>
          {units.map((x: any) => (
            <button key={x.unit} className={x.unit === unit ? 'btn' : 'btn ghost'} style={{ padding: '3px 10px' }}
              onClick={() => setChartUnit(x.unit)}>{unitChip(x.unit)} · {x.count} dòng</button>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, minmax(0, 1fr))', gap: 10, marginBottom: 10 }}>
        <Kpi label="Bình quân gia quyền" value={fmtUsd(kpi.wavg)} sub={`USD/${u} — theo lượng`} strong />
        <Kpi label="Khoảng giá phổ biến" value={kpi.p25 == null ? '—' : `${fmtUsd(kpi.p25)} – ${fmtUsd(kpi.p75)}`}
          sub="50% số dòng ở giữa" />
        <Kpi label="Thấp nhất" value={fmtUsd(kpi.min)} sub={`USD/${u}`} />
        <Kpi label="Cao nhất" value={fmtUsd(kpi.max)} sub={`USD/${u}`} />
        <Kpi label="Tổng lượng" value={fmtQty(kpi.qty)} sub={u} />
        <Kpi label="Số dòng hàng" value={String(kpi.count ?? 0)} sub="không phải số tờ khai" />
      </div>

      <div style={{ border: '1px solid #f5c26b', background: '#fff8e8', color: '#8a5a00', borderRadius: 8,
        padding: '8px 12px', fontSize: 13, marginBottom: 12 }}>
        <i className="ti ti-info-circle" /> Dựa trên {coverage.lines} dòng hàng trong {coverage.months} tháng
        ({fmtDate(coverage.date_from)} → {fmtDate(coverage.date_to)}).
        {coverage.empty_periods.length > 0 && <> Không có dữ liệu ở: {coverage.empty_periods.join(', ')}.</>}
        {years < 2
          ? <> Mới có dữ liệu <b>{years} năm</b> — chỉ thấy xu hướng trong năm, chưa đủ để kết luận theo mùa vụ.</>
          : <> Có dữ liệu {years} năm.</>}
        {' '}Kỳ dưới {minLines} dòng vẽ điểm rỗng và không được chọn làm kỳ giá tốt nhất.
        {kpi.outliers > 0 && (
          <> <b>{kpi.outliers} dòng giá bất thường</b> (nằm xa khoảng phổ biến — thường là gói nhỏ, hàng mẫu
            hoặc khai khác đơn vị) — biểu đồ không kéo trục theo chúng, xem cột Thấp nhất / Cao nhất.</>
        )}
      </div>

      <PriceAndQtyCharts series={series} best={best} unit={u} />

      <div className="card table-card" style={{ marginTop: 12 }}>
        <div className="table-scroll"><table>
          <thead><tr>
            <th>Kỳ</th><th style={{ textAlign: 'right' }}>Số dòng</th><th style={{ textAlign: 'right' }}>Tổng lượng ({u})</th>
            <th style={{ textAlign: 'right' }}>Bình quân gia quyền</th><th style={{ textAlign: 'right' }}>Khoảng phổ biến</th>
            <th style={{ textAlign: 'right' }}>Thấp nhất</th><th style={{ textAlign: 'right' }}>Cao nhất</th><th>Ghi chú</th>
          </tr></thead>
          <tbody>
            {series.map((s: any) => (
              <tr key={s.period} style={s.period === best ? { background: '#e8f7f0' } : undefined}>
                <td>{s.label}</td>
                <td style={{ textAlign: 'right' }}>{s.count}</td>
                <td style={{ textAlign: 'right' }}>{s.count ? fmtQty(s.qty) : '—'}</td>
                <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmtUsd(s.wavg)}</td>
                <td style={{ textAlign: 'right' }}>{s.p25 == null ? '—' : `${fmtUsd(s.p25)} – ${fmtUsd(s.p75)}`}</td>
                <td style={{ textAlign: 'right' }}>{fmtUsd(s.min)}</td>
                <td style={{ textAlign: 'right' }}>{fmtUsd(s.max)}</td>
                <td style={{ fontSize: 12, color: 'var(--muted)' }}>
                  {s.count === 0 ? 'Không có dữ liệu' : s.period === best ? 'Giá tốt nhất (đủ dữ liệu)' : s.low_data ? `Ít dữ liệu (< ${minLines} dòng)` : ''}
                </td>
              </tr>
            ))}
          </tbody>
        </table></div>
      </div>
    </div>
  )
}

function Seg({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: { value: string; label: string }[] }) {
  return (
    <span style={{ display: 'inline-flex', gap: 4, alignItems: 'center' }}>
      <span style={{ color: 'var(--muted)', marginRight: 2 }}>{label}:</span>
      {options.map((o) => (
        <button key={o.value} className={o.value === value ? 'btn' : 'btn ghost'} style={{ padding: '3px 10px' }}
          onClick={() => onChange(o.value)}>{o.label}</button>
      ))}
    </span>
  )
}

function Kpi({ label, value, sub, strong }: { label: string; value: string; sub?: string; strong?: boolean }) {
  return (
    <div className="card" style={{ padding: '10px 12px' }}>
      <div style={{ fontSize: 12, color: 'var(--muted)' }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color: strong ? 'var(--teal)' : undefined }}>{value}</div>
      {sub && <div style={{ fontSize: 11, color: 'var(--muted)' }}>{sub}</div>}
    </div>
  )
}

// Chia chuỗi điểm thành các đoạn LIÊN TỤC — kỳ trống cắt đoạn (luật 2).
function segments<T>(items: T[], ok: (x: T) => boolean): T[][] {
  const out: T[][] = []
  let cur: T[] = []
  for (const it of items) {
    if (ok(it)) cur.push(it)
    else if (cur.length) { out.push(cur); cur = [] }
  }
  if (cur.length) out.push(cur)
  return out
}

function PriceAndQtyCharts({ series, best, unit }: { series: any[]; best: string | null; unit: string }) {
  const { ref, width } = useWidth()
  const [hover, setHover] = useState<number | null>(null)
  const n = series.length
  const plotW = Math.max(width - PAD_L - PAD_R, 1)
  const slot = plotW / Math.max(n, 1)
  const cx = (i: number) => PAD_L + slot * (i + 0.5)
  // Nhãn trục ngang: nhiều kỳ quá thì thưa ra, tránh chữ đè nhau (mỗi nhãn cần ~64px).
  const labelEvery = Math.max(1, Math.ceil(64 / slot))

  // Trục giá theo bình quân + khoảng phổ biến, KHÔNG theo thấp / cao (luật 4).
  const vals = series.flatMap((s) => [s.wavg, s.p25, s.p75]).filter((v) => v != null) as number[]
  const ps = vals.length ? niceScale(Math.min(...vals) * 0.95, Math.max(...vals) * 1.05) : null
  const py = (v: number) => ps ? PRICE_T + (PRICE_H - PRICE_T - PRICE_B) * (1 - (v - ps.min) / (ps.max - ps.min || 1)) : 0

  const qs = niceScale(0, Math.max(1, ...series.map((s) => s.qty || 0)), 3)
  const qy = (v: number) => QTY_T + (QTY_H - QTY_T - QTY_B) * (1 - v / (qs.max || 1))
  const bw = Math.min(36, slot * 0.55)

  const pts = series.map((s, i) => ({ ...s, i }))
  const hs = hover != null ? series[hover] : null
  // Ô rê chuột: lệch sang trái khi điểm đang xem nằm nửa phải khung.
  const tipLeft = hover != null ? (cx(hover) > width / 2 ? cx(hover) - 12 - 250 : cx(hover) + 12) : 0

  const hitRects = (h: number) => series.map((s, i) => (
    <rect key={`h${s.period}`} x={PAD_L + slot * i} y={0} width={slot} height={h} fill="transparent"
      onMouseEnter={() => setHover(i)} />
  ))
  const guide = (h: number, top: number, bottom: number) => hover != null && (
    <line x1={cx(hover)} x2={cx(hover)} y1={top} y2={h - bottom} stroke="#94a3b8" strokeDasharray="3 3" pointerEvents="none" />
  )
  const xLabels = (h: number) => series.map((s, i) => (i % labelEvery === 0 || i === n - 1) && (
    <text key={`x${s.period}`} x={cx(i)} y={h - 8} textAnchor="middle" fontSize="11"
      fill={s.count ? (i === hover ? '#0f172a' : '#64748b') : '#b91c1c'} fontWeight={i === hover ? 600 : 400}>{s.label}</text>
  ))

  return (
    <div className="card" style={{ padding: 12, position: 'relative' }}>
      <Legend />
      <div ref={ref} style={{ position: 'relative' }} onMouseLeave={() => setHover(null)}>
        {width > 0 && (
          <>
            {ps ? (
              <svg width={width} height={PRICE_H} style={{ display: 'block' }} role="img" aria-label={`Giá USD/${unit} theo kỳ`}>
                {ps.ticks.map((t) => (
                  <g key={t}>
                    <line x1={PAD_L} x2={width - PAD_R} y1={py(t)} y2={py(t)} stroke="#eef2f6" />
                    <text x={PAD_L - 8} y={py(t) + 4} textAnchor="end" fontSize="11" fill="#64748b">{fmtTick(t)}</text>
                  </g>
                ))}
                <text x={4} y={PRICE_T + 4} fontSize="10.5" fill="#94a3b8">USD/{unit}</text>
                {series.map((s, i) => s.count === 0 && (
                  <rect key={`e${s.period}`} x={PAD_L + slot * i} y={PRICE_T} width={slot} height={PRICE_H - PRICE_T - PRICE_B}
                    fill="#fafafa" />
                ))}
                {segments(pts, (p) => p.p25 != null).map((seg, k) => seg.length === 1 ? (
                  <rect key={`b${k}`} x={cx(seg[0].i) - bw / 2} y={py(seg[0].p75)} width={bw}
                    height={Math.max(py(seg[0].p25) - py(seg[0].p75), 1)} fill={BAND} rx="3" />
                ) : (
                  <polygon key={`b${k}`} fill={BAND}
                    points={[...seg.map((p) => `${cx(p.i)},${py(p.p75)}`), ...seg.slice().reverse().map((p) => `${cx(p.i)},${py(p.p25)}`)].join(' ')} />
                ))}
                {guide(PRICE_H, PRICE_T, PRICE_B)}
                {segments(pts, (p) => p.wavg != null).map((seg, k) => (
                  <polyline key={`l${k}`} fill="none" stroke="var(--teal)" strokeWidth="2.2" strokeLinejoin="round"
                    points={seg.map((p) => `${cx(p.i)},${py(p.wavg)}`).join(' ')} />
                ))}
                {pts.filter((p) => p.wavg != null).map((p) => {
                  const isBest = p.period === best
                  const r = (isBest ? 6 : 4.5) + (p.i === hover ? 1.5 : 0)
                  return (
                    <circle key={p.period} cx={cx(p.i)} cy={py(p.wavg)} r={r} strokeWidth="2" pointerEvents="none"
                      stroke={isBest ? GREEN : 'var(--teal)'} fill={isBest ? GREEN : p.low_data ? '#fff' : 'var(--teal)'} />
                  )
                })}
                {xLabels(PRICE_H)}
                {hitRects(PRICE_H)}
              </svg>
            ) : <div style={{ color: 'var(--muted)', fontSize: 13, padding: 12 }}>Không có giá để vẽ.</div>}

            <div style={{ fontSize: 12, color: 'var(--muted)', margin: '10px 0 2px' }}>Lượng nhập ({unit})</div>
            <svg width={width} height={QTY_H} style={{ display: 'block' }} role="img" aria-label={`Lượng nhập (${unit}) theo kỳ`}>
              {qs.ticks.map((t) => (
                <g key={t}>
                  <line x1={PAD_L} x2={width - PAD_R} y1={qy(t)} y2={qy(t)} stroke={t === 0 ? '#cbd5e1' : '#eef2f6'} />
                  <text x={PAD_L - 8} y={qy(t) + 4} textAnchor="end" fontSize="11" fill="#64748b">{fmtCompact(t)}</text>
                </g>
              ))}
              {guide(QTY_H, QTY_T, QTY_B)}
              {series.map((s, i) => s.qty > 0 && (
                <rect key={s.period} x={cx(i) - bw / 2} y={qy(s.qty)} width={bw} height={Math.max(qy(0) - qy(s.qty), 1)} rx="3"
                  fill={s.period === best ? GREEN : i === hover ? '#94a3b8' : '#cbd5e1'} pointerEvents="none" />
              ))}
              {xLabels(QTY_H)}
              {hitRects(QTY_H)}
            </svg>

            {hs && (
              <div style={{ position: 'absolute', top: 8, left: Math.max(0, tipLeft), width: 250, pointerEvents: 'none',
                background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, boxShadow: '0 8px 24px rgba(15,23,42,.12)',
                padding: '8px 12px', fontSize: 12.5, zIndex: 2 }}>
                <div style={{ fontWeight: 700, marginBottom: 4 }}>
                  {hs.label}
                  {hs.period === best && <span style={{ color: GREEN, fontWeight: 600 }}> · giá tốt nhất</span>}
                  {hs.low_data && <span style={{ color: '#b45309', fontWeight: 600 }}> · ít dữ liệu</span>}
                </div>
                {hs.count === 0 ? <div style={{ color: 'var(--muted)' }}>Không có dòng hàng nào trong kỳ này</div> : (
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}><tbody>
                    <TipRow label="Bình quân gia quyền" value={`${fmtUsd(hs.wavg)} USD/${unit}`} strong />
                    <TipRow label="Khoảng phổ biến" value={hs.p25 == null ? '—' : `${fmtUsd(hs.p25)} – ${fmtUsd(hs.p75)}`} />
                    <TipRow label="Thấp nhất" value={fmtUsd(hs.min)} />
                    <TipRow label="Cao nhất" value={fmtUsd(hs.max)} />
                    <TipRow label="Số dòng hàng" value={String(hs.count)} />
                    <TipRow label="Tổng lượng" value={`${fmtQty(hs.qty)} ${unit}`} />
                  </tbody></table>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

function TipRow({ label, value, strong }: { label: string; value: string; strong?: boolean }) {
  return (
    <tr>
      <td style={{ color: 'var(--muted)', padding: '1px 0' }}>{label}</td>
      <td style={{ textAlign: 'right', padding: '1px 0', fontWeight: strong ? 700 : 500 }}>{value}</td>
    </tr>
  )
}

function Legend() {
  const item = (el: any, text: string) => <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>{el}{text}</span>
  return (
    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 12, color: 'var(--muted)', marginBottom: 6 }}>
      {item(<span style={{ width: 14, height: 2, background: 'var(--teal)' }} />, 'Bình quân gia quyền')}
      {item(<span style={{ width: 12, height: 10, background: BAND }} />, 'Khoảng giá phổ biến (50% số dòng ở giữa)')}
      {item(<span style={{ width: 9, height: 9, borderRadius: 9, border: '2px solid var(--teal)', background: '#fff' }} />, 'Ít dữ liệu')}
      {item(<span style={{ width: 10, height: 10, borderRadius: 10, background: GREEN }} />, 'Kỳ giá tốt nhất (đủ dữ liệu)')}
      <span>· Rê chuột lên biểu đồ để xem số của từng kỳ</span>
    </div>
  )
}
