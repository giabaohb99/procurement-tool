import type { CSSProperties, ReactNode } from 'react'
import { Link } from 'react-router-dom'
import {
  amountText, avgPriceText, diffColor, diffText, pctText, priceText, PKG_DOWN_COLOR, PKG_UP_COLOR, trendLabel, COST_TREND,
} from '../../utils/packaging-price'
import { historyHref, historyProductHref } from '../../utils/packaging-query'
import './packaging.css'

type Num = number | null | undefined

/** Ô chưa có giá: gạch mờ (khác với 0 đồng). */
export const Dash = () => <span className="pkg-muted">—</span>

/** Đơn giá (`fmtPrice`, đủ 4 số lẻ). */
export function PriceText({ value, bold, color, average }: { value: Num; bold?: boolean; color?: string; average?: boolean }) {
  const t = average ? avgPriceText(value) : priceText(value)
  if (!t) return <Dash />
  return <span className="pkg-num" style={{ fontWeight: bold ? 700 : undefined, color }}>{t}</span>
}

/** Thành tiền (`fmtVND`, làm tròn đồng). */
export function AmountText({ value }: { value: Num }) {
  const t = amountText(value)
  return t ? <span className="pkg-num">{t}</span> : <Dash />
}

/** Chênh lệch có dấu: tăng đỏ, giảm xanh, bằng 0 không màu. */
export function DiffText({ value, bold }: { value: Num; bold?: boolean }) {
  const t = diffText(value)
  if (!t) return <Dash />
  return <span className="pkg-num" style={{ fontWeight: bold ? 700 : undefined, color: diffColor(value) }}>{t}</span>
}

export function PctText({ value }: { value: Num }) {
  const t = pctText(value)
  if (!t) return <Dash />
  return <span className="pkg-num" style={{ color: diffColor(value) }}>{t}</span>
}

/**
 * Ô MÃ bấm được: mã VTBB mở Lịch sử mua hàng của đúng mã đó (`?codes=`); `product` = mã HÀNG HÓA, mở lịch sử ở chế độ
 * "Theo mã sản phẩm" (`?fg=`, mọi mã thành phần của định mức).
 */
export function CodeLink({ code, product }: { code: string; product?: boolean }) {
  return (
    <Link to={product ? historyProductHref(code) : historyHref(code)} className="pkg-code"
      title={product ? `Xem lịch sử mua các vật tư bao bì của ${code}` : `Xem lịch sử mua hàng của ${code}`}
      onClick={(e) => e.stopPropagation()}>
      {code}
    </Link>
  )
}

/** Xu hướng chi phí của một sản phẩm (mã `CostTrend`): tăng đỏ, giảm xanh (cùng luật với ô chênh lệch), còn lại màu mờ. */
export function TrendText({ trend }: { trend: number }) {
  const color = trend === COST_TREND.UP ? PKG_UP_COLOR : trend === COST_TREND.DOWN ? PKG_DOWN_COLOR : undefined
  return (
    <span className={color ? undefined : 'pkg-muted'} style={{ fontWeight: 600, color }}
      title={trend === COST_TREND.UP ? 'Chi phí tăng — cần xem lại giá bán' : undefined}>
      {trendLabel(trend)}
    </span>
  )
}

/** Tên một dòng, cắt bằng "…" — rê chuột hiện đủ (bảng không phình vì tên dài). */
export const OneLine = ({ children, title }: { children: ReactNode; title?: string }) => (
  <span className="pkg-oneline" title={title ?? (typeof children === 'string' ? children : undefined)}>{children}</span>
)

/** Tiêu đề cột bấm xếp (dùng cho các bảng tự dựng, như Giá mua gần nhất). */
export function SortTh({
  label, sortKey, sortBy, sortDir, onSort, align, style, className, rowSpan,
}: {
  label: ReactNode
  sortKey?: string
  sortBy: string
  sortDir: 'asc' | 'desc'
  onSort: (key: string) => void
  align?: 'left' | 'right' | 'center'
  style?: CSSProperties
  className?: string
  rowSpan?: number
}) {
  const active = !!sortKey && sortBy === sortKey
  const icon = active ? (sortDir === 'asc' ? 'ti-chevron-up' : 'ti-chevron-down') : 'ti-arrows-sort'
  return (
    <th rowSpan={rowSpan} className={(className || '') + (sortKey ? ' th-sortable' : '')}
      style={{ textAlign: align || 'left', ...style }}
      title={sortKey ? 'Bấm để sắp xếp' : undefined}
      onClick={sortKey ? () => onSort(sortKey) : undefined}>
      <span className="th-inner">
        <span className="th-label">{label}</span>
        {sortKey && <i className={`ti ${icon} th-sort-ico${active ? ' active' : ''}`} />}
      </span>
    </th>
  )
}
