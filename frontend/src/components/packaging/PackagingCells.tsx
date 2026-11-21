import type { CSSProperties, ReactNode } from 'react'
import { Link } from 'react-router-dom'
import {
  amountText, diffColor, diffText, pctText, priceText, PKG_DOWN_COLOR,
} from '../../utils/packaging-price'
import { historyHref } from '../../utils/packaging-query'
import './packaging.css'

type Num = number | null | undefined

/** Ô chưa có giá: gạch mờ (khác với 0 đồng). */
export const Dash = () => <span className="pkg-muted">—</span>

/** Đơn giá (`fmtPrice`, đủ 4 số lẻ). */
export function PriceText({ value, bold, color }: { value: Num; bold?: boolean; color?: string }) {
  const t = priceText(value)
  if (!t) return <Dash />
  return <span className="pkg-num" style={{ fontWeight: bold ? 700 : undefined, color }}>{t}</span>
}

/** Thành tiền (`fmtVND`, làm tròn đồng). */
export function AmountText({ value }: { value: Num }) {
  const t = amountText(value)
  return t ? <span className="pkg-num">{t}</span> : <Dash />
}

/** Chênh lệch có dấu: tăng xanh, giảm đỏ, bằng 0 không màu. */
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

/** Hai số "a – b" trong một ô (sàn–trần); cả hai trống thì gạch; `danger` tô đỏ khi giá ra ngoài ngưỡng. */
export function RangeText({ low, high, danger }: { low: Num; high: Num; danger?: boolean }) {
  const a = priceText(low)
  const b = priceText(high)
  if (!a && !b) return <Dash />
  return (
    <span className="pkg-num" style={danger ? { color: PKG_DOWN_COLOR, fontWeight: 700 } : undefined}>
      {a || '…'} – {b || '…'}
    </span>
  )
}

/** Ô MÃ VTBB bấm được: mở Lịch sử mua hàng của đúng mã đó (`?codes=`). */
export function CodeLink({ code }: { code: string }) {
  return (
    <Link to={historyHref(code)} className="pkg-code" title={`Xem lịch sử mua hàng của ${code}`}
      onClick={(e) => e.stopPropagation()}>
      {code}
    </Link>
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
