import type { ReactNode } from 'react'
import TableScroll from '../TableScroll'
import { CardSortBar } from '../TableCards'
import '../table-cards.css'
import { useNarrowScreen } from '../../hooks/useNarrowScreen'
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
  const narrow = useNarrowScreen()

  if (narrow) {
    return <LastPricesCards rows={rows} slots={slots} showQty={showQty} n={n} empty={empty} {...sort} />
  }

  return (
    <TableScroll>
      {/*  `--pkg-lp-code-w` = bề rộng cột Mã: cột Tên (dính trái thứ hai, 27/11/2026) đứng ngay sau nó khi cuộn ngang. */}
      <table className="dense pkg-lp" style={{ width: total, minWidth: total, ['--pkg-lp-code-w' as string]: `${W.code}px` }}>
        <colgroup>{widths.map((w, i) => <col key={i} style={{ width: w }} />)}</colgroup>
        <thead>
          <tr>
            {/* Ô đầu (cột Mã dính trái) để trống: ô gộp 5 cột mà dính trái thì phủ lên các cột khác khi cuộn ngang. */}
            <th className="sticky-col" />
            {/*  Nhãn nhóm nằm trên cột Tên (cũng dính trái) để không trôi mất khi cuộn ngang. */}
            <th className="sticky-col-2" style={{ textAlign: 'left' }}>Thông tin VTBB</th>
            <th colSpan={infoCols - 2} />
            {slots.map((i) => (
              <th key={i} colSpan={perSlot} className={`${TONES[i % TONES.length]} gsep`}>{purchaseGroupLabel(i)}</th>
            ))}
            <th colSpan={2} className="gsep">Biến động</th>
            <th className="gsep">Giá TB</th>
          </tr>
          <tr>
            <SortTh label="Mã VTBB" sortKey="code" className="sticky-col" {...sort} />
            <SortTh label="Tên vật tư" sortKey="name" className="sticky-col-2" {...sort} />
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
              <td className="sticky-col-2" title={r.name}>{r.name || <span className="pkg-muted">(chưa có tên)</span>}</td>
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
              <td style={{ textAlign: 'right' }}><PriceText value={r.avg} bold average /></td>
            </tr>
          ))}
          {rows.length === 0 && <tr><td colSpan={colCount} className="table-empty">{empty}</td></tr>}
        </tbody>
      </table>
    </TableScroll>
  )
}

/**
 * Màn hẹp: mỗi mã một thẻ — mã + tên, ba số chính (giá TB, lần 1 so lần 2, lần 1 so lần n), nhóm / ĐVT / số lần có giá,
 * rồi danh sách n lần mua gọn (ngày · đơn giá, dòng dưới nhà cung cấp + số lượng). Màu nền từng lần y tiêu đề bảng; đơn giá
 * tô xanh / đỏ so với lần mua liền trước như ô bảng. Nhãn trùng tiêu đề bảng.
 */
function LastPricesCards({ rows, slots, showQty, n, empty, sortBy, sortDir, onSort }: {
  rows: PackagingLastPricesRow[]
  slots: number[]
  showQty: boolean
  n: number
  empty: ReactNode
  sortBy: string
  sortDir: 'asc' | 'desc'
  onSort: (key: string) => void
}) {
  const options = [
    { key: 'code', label: 'Mã VTBB' }, { key: 'name', label: 'Tên vật tư' }, { key: 'group', label: 'Nhóm' },
    { key: 'purchase_count', label: 'Số lần có giá' },
    ...slots.flatMap((i) => [
      { key: `p${i + 1}_date`, label: `${purchaseGroupLabel(i)} — Ngày mua` },
      { key: `p${i + 1}_price`, label: `${purchaseGroupLabel(i)} — Đơn giá` },
    ]),
    { key: 'v12', label: 'Lần 1 so lần 2' }, { key: 'v1n', label: `Lần 1 so lần ${n}` }, { key: 'avg', label: `Giá TB ${n} lần` },
  ]
  return (
    <div className="tcards-wrap">
      <CardSortBar options={options} sortBy={sortBy} sortDir={sortDir} onSort={onSort} />
      {rows.length === 0 && <div className="tcards-empty">{empty}</div>}
      <ul className="tcards">
        {rows.map((r) => (
          <li key={r.code} className="tcard">
            <div className="tcard-head"><div className="tcard-title"><CodeLink code={r.code} /></div></div>
            <div className="tcard-sub">{r.name || <span className="pkg-muted">(chưa có tên)</span>}</div>
            <div className="tcard-heroes" style={{ gridTemplateColumns: 'repeat(3, minmax(0, 1fr))' }}>
              <div className="tcard-hero"><span className="tcard-k">{`Giá TB ${n} lần`}</span><span className="tcard-v"><PriceText value={r.avg} bold average /></span></div>
              <div className="tcard-hero"><span className="tcard-k">Lần 1 so lần 2</span><span className="tcard-v"><PctText value={r.v12} /></span></div>
              <div className="tcard-hero"><span className="tcard-k">{`Lần 1 so lần ${n}`}</span><span className="tcard-v"><PctText value={r.v1n} /></span></div>
            </div>
            <dl className="tcard-grid" style={{ gridTemplateColumns: '1fr 1fr 1fr' }}>
              <div className="tcard-f"><dt>Nhóm</dt><dd>{r.group || <Dash />}</dd></div>
              <div className="tcard-f"><dt>ĐVT</dt><dd>{r.unit || <Dash />}</dd></div>
              <div className="tcard-f"><dt>Số lần có giá</dt><dd>{r.purchase_count}</dd></div>
            </dl>
            <div className="tcard-buys">
              {slots.map((i) => {
                const p = purchaseAt(r, i)
                //  Lần chưa có giá mua: một dòng mờ, không chiếm cả ô màu.
                if (!p) return <div key={i} className="tcard-buy empty">{purchaseGroupLabel(i)} · chưa có lần mua</div>
                return (
                  <div key={i} className={`tcard-buy ${TONES[i % TONES.length]}`}>
                    <div className="tcard-buy-top">
                      <span>{purchaseGroupLabel(i)} · {p?.date ? fmtDateStr(p.date) : <Dash />}</span>
                      <b><PriceText value={p?.price} bold color={purchaseTone(r, i)} /></b>
                    </div>
                    {p && (p.supplier || (showQty && qtyText(p.qty))) && (
                      <div className="tcard-buy-sub">{[p.supplier, showQty ? (qtyText(p.qty) ? `SL ${qtyText(p.qty)}` : '') : ''].filter(Boolean).join(' · ')}</div>
                    )}
                  </div>
                )
              })}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
