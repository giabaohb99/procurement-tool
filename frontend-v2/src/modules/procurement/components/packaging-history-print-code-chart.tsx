/**
 * duoc-CR-784 — biểu đồ "Diễn biến đơn giá theo thành phần (VNĐ)" của bản in Lịch sử mua hàng (đúng một sản phẩm, chế độ sản phẩm):
 * mỗi mã thành phần một đường, chú giải = vai trò + mã. SVG tĩnh cùng khuôn với `PrintPriceChart` (recharts đo khung bằng JS lúc
 * chạy nên không đáng tin ở khổ giấy); hàng dữ liệu + kiểu đường dùng chung với biểu đồ màn hình (`packaging-history-series.ts`).
 */
import { formatDate } from '@/shared/utils/format-date'

import type { PackagingHistorySeriesLine } from '../types/packaging-cost-types'
import { dateTickAnchor, pickDateTickIndexes } from '../utils/packaging-chart-date-ticks'
import {
  assignHistoryLineStyles,
  buildSeriesRows,
  historyLineKey,
  historyLineLegend,
  seriesAxisDomain,
} from '../utils/packaging-history-series'

const CHART = { width: 1000, height: 200, left: 52, right: 14, top: 16, bottom: 30 }

/** "30/06/2026" -> "30/06/26" — nhãn trục ngày của bản mẫu. */
function shortDate(iso: string): string {
  const full = formatDate(iso)
  return full.length === 10 ? `${full.slice(0, 6)}${full.slice(8)}` : full
}

export function PrintCodeChart({ lines }: { lines: readonly PackagingHistorySeriesLine[] }) {
  const rows = buildSeriesRows(lines)
  if (rows.length === 0) return null
  const { width: W, height: H, left, right, top, bottom } = CHART
  const styles = assignHistoryLineStyles(lines)
  const [y0, y1] = seriesAxisDomain(lines)
  const x = (i: number) =>
    rows.length === 1 ? (left + W - right) / 2 : left + (i * (W - left - right)) / (rows.length - 1)
  const y = (value: number) => top + (H - top - bottom) * (1 - (value - y0) / (y1 - y0))
  const step = Math.max(1, Math.ceil(rows.length / 10))
  //  Nhãn ngày thưa theo độ rộng thật: không để hai nhãn (nhất là nhãn cuối) đè lên nhau.
  const tickLabels = rows.map((row) => shortDate(row.date))
  const tickIndexes = pickDateTickIndexes(rows.map((_, i) => x(i)), tickLabels, step)
  return (
    <div className="panel chart">
      <h4>Diễn biến đơn giá theo thành phần (VNĐ)</h4>
      <ul
        aria-label="Chú giải"
        style={{ display: 'flex', flexWrap: 'wrap', gap: '4px 16px', margin: '0 0 4px', padding: 0, listStyle: 'none', fontSize: 12 }}
      >
        {lines.map((line, index) => (
          <li key={line.code} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <svg width="18" height="8" aria-hidden>
              <line x1="0" x2="18" y1="4" y2="4" stroke={styles[index].print} strokeWidth="2.5" strokeDasharray={styles[index].dash || undefined} />
            </svg>
            {historyLineLegend(line)}
          </li>
        ))}
      </ul>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Diễn biến đơn giá theo thành phần">
        {[y0, (y0 + y1) / 2, y1].map((value) => (
          <g key={value}>
            <line x1={left} x2={W - right} y1={y(value)} y2={y(value)} stroke="#EEF1F5" />
            <text x={left - 8} y={y(value) + 4} textAnchor="end" fontSize="11" fill="#8C939C">
              {Math.round(value).toLocaleString('vi-VN')}
            </text>
          </g>
        ))}
        {lines.map((line, index) => {
          const key = historyLineKey(index)
          //  Chỉ nối các hàng đường này có lần mua (nối qua hàng trống như biểu đồ màn hình).
          const dots = rows.flatMap((row, i) => (typeof row[key] === 'number' ? [{ i, price: row[key] as number }] : []))
          const path = dots.map((d, n) => `${n ? 'L' : 'M'}${x(d.i).toFixed(1)},${y(d.price).toFixed(1)}`).join(' ')
          const { print, dash } = styles[index]
          return (
            <g key={line.code} data-line={line.code}>
              <path d={path} fill="none" stroke={print} strokeWidth="2.2" strokeDasharray={dash || undefined} />
              {dots.map((d) => (
                <circle key={d.i} cx={x(d.i)} cy={y(d.price)} r="3.5" fill="#fff" stroke={print} strokeWidth="2" />
              ))}
            </g>
          )
        })}
        {tickIndexes.map((i) => (
          <text key={`t${i}`} x={x(i)} y={H - 8} textAnchor={dateTickAnchor(i, rows.length)} fontSize="11" fill="#5A5A5A">
            {tickLabels[i]}
          </text>
        ))}
      </svg>
    </div>
  )
}
