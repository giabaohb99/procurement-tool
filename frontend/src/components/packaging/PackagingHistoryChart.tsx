import { useLayoutEffect, useMemo, useRef, useState } from 'react'
import type { PackagingHistoryPoint } from '../../api/packaging-cost-types'
import { fmtDateStr } from '../../utils/datetime'
import { priceText, qtyText } from '../../utils/packaging-price'
import { priceAxisDomain } from '../../utils/packaging-query'
import './packaging.css'

const HEIGHT = 150
const PAD = { left: 64, right: 16, top: 8, bottom: 22 }
const X_LABELS = 6   // số nhãn ngày tối đa trên trục ngang
const Y_TICKS = 4

/**
 * Biểu đồ "Diễn biến đơn giá qua các lần mua": một đường theo thứ tự các lần mua CÓ GIÁ của đúng một mã, cũ → mới.
 * Vẽ bằng SVG thuần (v1 không có thư viện biểu đồ, và không thêm phụ thuộc mới). Trục giá KHÔNG bắt đầu từ 0 (xem
 * `priceAxisDomain`) và mỗi lần mua là một chấm — giá đi ngang vài tháng rồi nhích 3% vẫn nhìn ra. Rê chuột hiện chi tiết.
 */
export default function PackagingHistoryChart({ series, subject }: { series: readonly PackagingHistoryPoint[]; subject?: string }) {
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

  const geo = useMemo(() => {
    const [lo, hi] = priceAxisDomain(series)
    const innerW = width - PAD.left - PAD.right
    const innerH = HEIGHT - PAD.top - PAD.bottom
    const n = series.length
    const x = (i: number) => PAD.left + (n === 1 ? innerW / 2 : (i * innerW) / (n - 1))
    const y = (p: number) => PAD.top + ((hi - p) / (hi - lo || 1)) * innerH
    const path = series.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(i).toFixed(1)},${y(p.price).toFixed(1)}`).join(' ')
    const yTicks = Array.from({ length: Y_TICKS }, (_, k) => lo + ((hi - lo) * k) / (Y_TICKS - 1))
    const step = Math.max(1, Math.ceil(n / X_LABELS))
    //  Nhãn ngày cách đều theo bước; nhãn cuối luôn có (thay nhãn kế cuối nếu hai nhãn chen nhau).
    const xLabels: number[] = []
    for (let i = 0; i < n; i += step) xLabels.push(i)
    const last = xLabels[xLabels.length - 1]
    if (last !== n - 1) {
      if (n - 1 - last < step / 2) xLabels[xLabels.length - 1] = n - 1
      else xLabels.push(n - 1)
    }
    return { x, y, path, yTicks, xLabels }
  }, [series, width])

  function onMove(e: React.MouseEvent<SVGSVGElement>) {
    const rect = e.currentTarget.getBoundingClientRect()
    const px = e.clientX - rect.left
    let best = 0
    series.forEach((_, i) => { if (Math.abs(geo.x(i) - px) < Math.abs(geo.x(best) - px)) best = i })
    setHover(best)
  }

  const point = hover != null ? series[hover] : null
  const tipLeft = hover != null ? Math.min(geo.x(hover) + 12, width - 190) : 0

  return (
    <div className="pkg-chart" ref={boxRef}>
      <div className="pkg-chart-title">
        Diễn biến đơn giá qua các lần mua (VNĐ){subject && ` — ${subject}`} <span>({series.length} lần có giá)</span>
      </div>
      <svg width={width} height={HEIGHT} role="img" aria-label="Biểu đồ diễn biến đơn giá" onMouseMove={onMove} onMouseLeave={() => setHover(null)}>
        {geo.yTicks.map((t) => (
          <g key={t}>
            <line x1={PAD.left} x2={width - PAD.right} y1={geo.y(t)} y2={geo.y(t)} stroke="#e9edf7" />
            <text x={PAD.left - 8} y={geo.y(t) + 4} textAnchor="end" fontSize="11" fill="#64748b">{priceText(Math.round(t))}</text>
          </g>
        ))}
        {geo.xLabels.map((i) => (
          <text key={i} x={geo.x(i)} y={HEIGHT - 6} textAnchor={i === 0 ? 'start' : i === series.length - 1 ? 'end' : 'middle'} fontSize="11" fill="#64748b">
            {fmtDateStr(series[i].date)}
          </text>
        ))}
        <path d={geo.path} fill="none" stroke="var(--teal)" strokeWidth="2" strokeLinejoin="round" />
        {series.map((p, i) => (
          <circle key={i} cx={geo.x(i)} cy={geo.y(p.price)} r={hover === i ? 5 : 3} fill="var(--teal)" stroke="#fff" strokeWidth="1.5" />
        ))}
        {hover != null && <line x1={geo.x(hover)} x2={geo.x(hover)} y1={PAD.top} y2={HEIGHT - PAD.bottom} stroke="#cbd5e1" />}
      </svg>
      {point && (
        <div className="pkg-chart-tip" style={{ left: tipLeft, top: 26 }}>
          <b>{fmtDateStr(point.date)}</b>
          <div><span className="pkg-muted">Đơn giá</span><span>{priceText(point.price)}</span></div>
          <div><span className="pkg-muted">Số lượng</span><span>{qtyText(point.qty) || '—'}</span></div>
          <div><span className="pkg-muted">Nhà cung cấp</span><span style={{ maxWidth: 110, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{point.supplier || '—'}</span></div>
        </div>
      )}
    </div>
  )
}
