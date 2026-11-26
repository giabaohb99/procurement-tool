import type { PackagingHistorySeriesByCode } from '../../api/packaging-cost-types'
import { fmtDateStr } from '../../utils/datetime'
import { dateTickAnchor, pickDateTickIndexes } from '../../utils/packaging-chart-date-ticks'
import { buildSeriesPath, collectSeriesDates, seriesColor, seriesLabel } from '../../utils/packaging-multi-series-chart'

const CHART = { w: 1000, h: 220, l: 52, r: 14, t: 30, b: 30 }

/** "2026-06-30" -> "30/06/26" — nhãn trục ngày của bản mẫu (cùng `PrintPriceChart`). */
const shortDate = (iso: string): string => { const d = fmtDateStr(iso); return d.length === 10 ? `${d.slice(0, 6)}${d.slice(8)}` : d }

/**
 * Bản in của biểu đồ nhiều đường (một sản phẩm, mỗi mã thành phần một đường): cùng khung, màu trục và cỡ chữ với
 * `PrintPriceChart`; chú giải vẽ ngay trong SVG (nền màu của thẻ HTML hay bị trình duyệt bỏ khi in). `series` đã qua
 * `normalizeSeriesByCode`.
 */
export function PrintMultiPriceChart({ series, subject }: { series: readonly PackagingHistorySeriesByCode[]; subject?: string }) {
  const dates = collectSeriesDates(series)
  if (dates.length === 0) return null
  const { w: W, h: H, l, r, t, b } = CHART
  const prices = series.flatMap((s) => s.points.map((p) => p.price))
  const lo = Math.min(...prices)
  const hi = Math.max(...prices)
  const pad = (hi - lo) * 0.15 || hi * 0.05 || 1
  const y0 = Math.max(0, lo - pad)
  const y1 = hi + pad
  const x = (i: number) => (dates.length === 1 ? (l + W - r) / 2 : l + (i * (W - l - r)) / (dates.length - 1))
  const y = (v: number) => t + (H - t - b) * (1 - (v - y0) / (y1 - y0))
  const step = Math.max(1, Math.ceil(dates.length / 10))
  const tickLabels = dates.map(shortDate)
  const tickIndexes = pickDateTickIndexes(dates.map((_, i) => x(i)), tickLabels, step)
  const money = (v: number) => Math.round(v).toLocaleString('vi-VN')
  //  Chú giải: mỗi mục rộng theo độ dài chữ (ước 7px / ký tự ở cỡ 12) + vạch màu 18px.
  let legendX = l
  const legend = series.map((s, k) => {
    const label = seriesLabel(s)
    const item = { s, k, label, x: legendX }
    legendX += 18 + 6 + label.length * 7 + 22
    return item
  })
  return (
    <div className="panel chart">
      <h4>Diễn biến đơn giá các thành phần (VNĐ){subject && ` — ${subject}`}</h4>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Diễn biến đơn giá các thành phần">
        {legend.map(({ k, label, x: lx }) => (
          <g key={label}>
            <line x1={lx} x2={lx + 18} y1={10} y2={10} stroke={seriesColor(k)} strokeWidth="3" strokeLinecap="round" />
            <text x={lx + 24} y={14} fontSize="12" fill="#0F3B6E">{label}</text>
          </g>
        ))}
        {[y0, (y0 + y1) / 2, y1].map((v) => (
          <g key={v}>
            <line x1={l} x2={W - r} y1={y(v)} y2={y(v)} stroke="#EEF1F5" />
            <text x={l - 8} y={y(v) + 4} textAnchor="end" fontSize="11" fill="#8C939C">{money(v)}</text>
          </g>
        ))}
        {series.map((s, k) => (
          <g key={s.code}>
            <path d={buildSeriesPath(s, dates, x, y)} fill="none" stroke={seriesColor(k)} strokeWidth="2.2" />
            {s.points.map((p, j) => (
              <circle key={j} cx={x(dates.indexOf(p.date))} cy={y(p.price)} r="3.5" fill="#fff" stroke={seriesColor(k)} strokeWidth="2" />
            ))}
          </g>
        ))}
        {tickIndexes.map((i) => (
          <text key={`t${i}`} x={x(i)} y={H - 8} fontSize="11" fill="#5A5A5A" textAnchor={dateTickAnchor(i, dates.length)}>
            {tickLabels[i]}
          </text>
        ))}
      </svg>
    </div>
  )
}
