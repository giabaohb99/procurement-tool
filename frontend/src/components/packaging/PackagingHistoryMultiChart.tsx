import { useLayoutEffect, useMemo, useRef, useState } from 'react'
import type { PackagingHistorySeriesByCode } from '../../api/packaging-cost-types'
import { fmtDateStr } from '../../utils/datetime'
import {
  buildSeriesPath, collectSeriesDates, priceOnDate, seriesColor, seriesLabel,
} from '../../utils/packaging-multi-series-chart'
import { priceText } from '../../utils/packaging-price'
import { priceAxisDomain } from '../../utils/packaging-query'
import './packaging.css'

const HEIGHT = 170
const PAD = { left: 64, right: 16, top: 8, bottom: 22 }
const X_LABELS = 6   // số nhãn ngày tối đa trên trục ngang
const Y_TICKS = 4

/**
 * Biểu đồ "Diễn biến đơn giá các thành phần" của MỘT sản phẩm (chế độ "Theo mã sản phẩm"): mỗi mã thành phần một đường, chú
 * giải ghi thành phần + mã. Cùng kiểu dáng với `PackagingHistoryChart` (SVG thuần, trục giá không bắt đầu từ 0, rê chuột hiện
 * giá từng thành phần tại ngày gần nhất). `series` đã qua `normalizeSeriesByCode`.
 */
export default function PackagingHistoryMultiChart({ series, subject }: { series: readonly PackagingHistorySeriesByCode[]; subject?: string }) {
  const boxRef = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(640)
  const [hover, setHover] = useState<number | null>(null)

  useLayoutEffect(() => {
    const el = boxRef.current
    if (!el) return
    const measure = () => setWidth(Math.max(320, el.clientWidth))
    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const dates = useMemo(() => collectSeriesDates(series), [series])
  const geo = useMemo(() => {
    const [lo, hi] = priceAxisDomain(series.flatMap((s) => s.points))
    const innerW = width - PAD.left - PAD.right
    const innerH = HEIGHT - PAD.top - PAD.bottom
    const n = dates.length
    const x = (i: number) => PAD.left + (n === 1 ? innerW / 2 : (i * innerW) / (n - 1))
    const y = (p: number) => PAD.top + ((hi - p) / (hi - lo || 1)) * innerH
    const paths = series.map((s) => buildSeriesPath(s, dates, x, y))
    const yTicks = Array.from({ length: Y_TICKS }, (_, k) => lo + ((hi - lo) * k) / (Y_TICKS - 1))
    const step = Math.max(1, Math.ceil(n / X_LABELS))
    const xLabels: number[] = []
    for (let i = 0; i < n; i += step) xLabels.push(i)
    const last = xLabels[xLabels.length - 1]
    if (last !== n - 1) {
      if (n - 1 - last < step / 2) xLabels[xLabels.length - 1] = n - 1
      else xLabels.push(n - 1)
    }
    return { x, y, paths, yTicks, xLabels }
  }, [series, dates, width])

  function onMove(e: React.MouseEvent<SVGSVGElement>) {
    const px = e.clientX - e.currentTarget.getBoundingClientRect().left
    let best = 0
    dates.forEach((_, i) => { if (Math.abs(geo.x(i) - px) < Math.abs(geo.x(best) - px)) best = i })
    setHover(best)
  }

  const hoverDate = hover != null ? dates[hover] : null
  const tipLeft = hover != null ? Math.min(geo.x(hover) + 12, width - 230) : 0

  return (
    <div className="pkg-chart" ref={boxRef}>
      <div className="pkg-chart-title">
        Diễn biến đơn giá các thành phần (VNĐ){subject && ` — ${subject}`} <span>({series.length} mã, {dates.length} ngày mua)</span>
      </div>
      <div className="pkg-chart-legend" aria-label="Chú giải biểu đồ">
        {series.map((s, k) => (
          <span key={s.code} title={s.name || undefined}>
            <i style={{ background: seriesColor(k) }} />{seriesLabel(s)}
          </span>
        ))}
      </div>
      <svg width={width} height={HEIGHT} role="img" aria-label="Biểu đồ diễn biến đơn giá các thành phần" onMouseMove={onMove} onMouseLeave={() => setHover(null)}>
        {geo.yTicks.map((t) => (
          <g key={t}>
            <line x1={PAD.left} x2={width - PAD.right} y1={geo.y(t)} y2={geo.y(t)} stroke="#e9edf7" />
            <text x={PAD.left - 8} y={geo.y(t) + 4} textAnchor="end" fontSize="11" fill="#64748b">{priceText(Math.round(t))}</text>
          </g>
        ))}
        {geo.xLabels.map((i) => (
          <text key={i} x={geo.x(i)} y={HEIGHT - 6} textAnchor={i === 0 ? 'start' : i === dates.length - 1 ? 'end' : 'middle'} fontSize="11" fill="#64748b">
            {fmtDateStr(dates[i])}
          </text>
        ))}
        {hover != null && <line x1={geo.x(hover)} x2={geo.x(hover)} y1={PAD.top} y2={HEIGHT - PAD.bottom} stroke="#cbd5e1" />}
        {series.map((s, k) => (
          <g key={s.code}>
            <path d={geo.paths[k]} fill="none" stroke={seriesColor(k)} strokeWidth="2" strokeLinejoin="round" />
            {s.points.map((p, j) => (
              <circle key={j} cx={geo.x(dates.indexOf(p.date))} cy={geo.y(p.price)} r={hoverDate === p.date ? 5 : 3}
                fill={seriesColor(k)} stroke="#fff" strokeWidth="1.5" />
            ))}
          </g>
        ))}
      </svg>
      {hoverDate && (
        <div className="pkg-chart-tip" style={{ left: tipLeft, top: 48 }}>
          <b>{fmtDateStr(hoverDate)}</b>
          {series.map((s, k) => {
            const price = priceOnDate(s, hoverDate)
            return (
              <div key={s.code}>
                <span className="pkg-muted"><i className="pkg-chart-dot" style={{ background: seriesColor(k) }} />{seriesLabel(s)}</span>
                <span>{price === undefined ? '—' : priceText(price)}</span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
