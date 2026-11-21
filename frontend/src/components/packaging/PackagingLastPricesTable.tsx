import type { ReactNode } from 'react'
import TableScroll from '../TableScroll'
import type { PackagingLastPricesRow } from '../../api/packaging-cost-types'
import { fmtDateStr } from '../../utils/datetime'
import { qtyText } from '../../utils/packaging-price'
import { purchaseAt, purchaseGroupLabel, purchaseTone } from '../../utils/packaging-query'
import { CodeLink, Dash, PctText, PriceText, SortTh } from './PackagingCells'
import './packaging.css'

/** Mỗi cụm "Lần" một màu tiêu đề (nhạt, vòng 4 màu: xanh dương → cam → xanh lá → hổ phách); thân bảng để trắng. */
const TONES = ['g0', 'g1', 'g2', 'g3']

/** Bề rộng cột (px) — bảng `table-layout: fixed` nên mọi ô MỘT dòng, cắt bằng "…" (đủ chữ ở tooltip `title`). */
const W = { code: 110, name: 280, group: 90, unit: 64, count: 110, date: 100, supplier: 220, qty: 90, price: 110, var: 130, avg: 120 }

/**
 * Bảng GIÁ MUA GẦN NHẤT: tiêu đề HAI hàng — hàng trên gộp nhóm ("Thông tin VTBB" | "Lần 1 (gần nhất)" … "Lần n" |
 * "Biến động" | "Giá TB"), hàng dưới là cột con bấm xếp được. Cột Mã dính trái khi cuộn ngang; vạch 1px ngăn các nhóm
 * chỉ nằm ở tiêu đề.
 */
export default function PackagingLastPricesTable({
  rows, n, showQty, sortBy, sortDir, onSort, empty,
}: {
  rows: PackagingLastPricesRow[]
  n: number
  showQty: boolean
  sortBy: string
  sortDir: 'asc' | 'desc'
  onSort: (key: string) => void
  empty: ReactNode
}) {
  const sort = { sortBy, sortDir, onSort }
  const slots = Array.from({ length: n }, (_, i) => i)
  const perSlot = showQty ? 4 : 3
  const infoCols = 5
  const colCount = infoCols + n * perSlot + 3
  const widths = [
    W.code, W.name, W.group, W.unit, W.count,
    ...slots.flatMap(() => [W.date, W.supplier, ...(showQty ? [W.qty] : []), W.price]),
    W.var, W.var, W.avg,
  ]
  const total = widths.reduce((s, w) => s + w, 0)

  return (
    <TableScroll>
      <table className="dense pkg-lp" style={{ width: total, minWidth: total }}>
        <colgroup>{widths.map((w, i) => <col key={i} style={{ width: w }} />)}</colgroup>
        <thead>
          <tr>
            {/* Ô đầu (cột Mã dính trái) để trống: ô gộp 5 cột mà dính trái thì phủ lên các cột khác khi cuộn ngang. */}
            <th className="sticky-col" />
            <th colSpan={infoCols - 1} style={{ textAlign: 'left' }}>Thông tin VTBB</th>
            {slots.map((i) => (
              <th key={i} colSpan={perSlot} className={`${TONES[i % TONES.length]} gsep`}>{purchaseGroupLabel(i)}</th>
            ))}
            <th colSpan={2} className="gsep">Biến động</th>
            <th className="gsep">Giá TB</th>
          </tr>
          <tr>
            <SortTh label="Mã VTBB" sortKey="code" className="sticky-col" {...sort} />
            <SortTh label="Tên vật tư" sortKey="name" {...sort} />
            <SortTh label="Nhóm" sortKey="group" {...sort} />
            <SortTh label="ĐVT" {...sort} />
            <SortTh label="Số lần có giá" sortKey="purchase_count" align="right" {...sort} />
            {slots.flatMap((i) => {
              const tone = TONES[i % TONES.length]
              const k = i + 1
              return [
                <SortTh key={`d${i}`} label="Ngày mua" sortKey={`p${k}_date`} className={`${tone} gsep`} {...sort} />,
                <SortTh key={`s${i}`} label="Nhà cung cấp" className={tone} {...sort} />,
                ...(showQty ? [<SortTh key={`q${i}`} label="Số lượng" align="right" className={tone} {...sort} />] : []),
                <SortTh key={`p${i}`} label="Đơn giá" sortKey={`p${k}_price`} align="right" className={tone} {...sort} />,
              ]
            })}
            <SortTh label="Lần 1 so lần 2" sortKey="v12" align="right" className="gsep" {...sort} />
            <SortTh label={`Lần 1 so lần ${n}`} sortKey="v1n" align="right" {...sort} />
            <SortTh label={`Giá TB ${n} lần`} sortKey="avg" align="right" className="gsep" {...sort} />
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.code}>
              <td className="sticky-col"><CodeLink code={r.code} /></td>
              <td title={r.name}>{r.name || <span className="pkg-muted">(chưa có tên)</span>}</td>
              <td>{r.group}</td>
              <td>{r.unit}</td>
              <td style={{ textAlign: 'right' }}>{r.purchase_count}</td>
              {slots.flatMap((i) => {
                const p = purchaseAt(r, i)
                return [
                  <td key={`d${i}`}>{p?.date ? fmtDateStr(p.date) : <Dash />}</td>,
                  <td key={`s${i}`} title={p?.supplier || undefined}>{p?.supplier || <Dash />}</td>,
                  ...(showQty ? [<td key={`q${i}`} style={{ textAlign: 'right' }}>{qtyText(p?.qty) || <Dash />}</td>] : []),
                  <td key={`p${i}`} style={{ textAlign: 'right' }}><PriceText value={p?.price} bold color={purchaseTone(r, i)} /></td>,
                ]
              })}
              <td style={{ textAlign: 'right' }}><PctText value={r.v12} /></td>
              <td style={{ textAlign: 'right' }}><PctText value={r.v1n} /></td>
              <td style={{ textAlign: 'right' }}><PriceText value={r.avg} bold /></td>
            </tr>
          ))}
          {rows.length === 0 && <tr><td colSpan={colCount} className="table-empty">{empty}</td></tr>}
        </tbody>
      </table>
    </TableScroll>
  )
}
