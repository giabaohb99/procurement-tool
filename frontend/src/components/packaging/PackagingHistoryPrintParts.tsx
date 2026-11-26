import type { PackagingHistoryMode, PackagingHistoryPoint, PackagingHistoryRow } from '../../api/packaging-cost-types'
import { fmtDateStr } from '../../utils/datetime'
import { dateTickAnchor, pickDateTickIndexes } from '../../utils/packaging-chart-date-ticks'
import { amountText, diffText, pctText, priceText, qtyText } from '../../utils/packaging-price'
import { historyRoleText, historyRowKey } from '../../utils/packaging-query'
import { PrintDash } from './PackagingPrintShell'
import { PrintChipsBox } from './PackagingPrintWidgets'

/**
 * duoc-CR-784 — các khối của bản in Lịch sử mua hàng (bản v1), dựng theo bản mẫu HTML: ô lọc + dòng thông tin, biểu đồ đơn
 * giá (đường xanh lá đậm, chấm trắng viền xanh, chấm cuối xanh dương kèm số, đúng hàm `drawChart` của bản mẫu), bảng lần mua
 * đầu navy. Số liệu + khuôn định dạng dùng lại đúng hàm của màn hình nên bản in không lệch con số với màn.
 */

/** Khối ô lọc: hai chip chế độ + ô mã + dòng thông tin (cùng cấu trúc `.filters` + `.info` của bản mẫu). */
export function PrintHistoryFilters({ mode, codes, first, singleCode, extras }: {
  mode: PackagingHistoryMode
  codes: readonly string[]
  /** Dòng đầu của bảng — lấy tên / nhóm / ĐVT khi đúng một mã. */
  first: PackagingHistoryRow | undefined
  singleCode: boolean
  /** Các điều kiện còn lại đang bật (NCC, khoảng ngày, từ khóa) — từ `describeHistoryFilters`. */
  extras: readonly string[]
}) {
  const isProduct = mode === 'product'
  const scope = singleCode && first ? (
    <><b>{first.code}</b> — {first.name || '(chưa có tên)'}{first.group && ` · ${first.group}`}{first.unit && ` · ĐVT ${first.unit}`}</>
  ) : codes.length ? (
    <>Đã chọn <b>{codes.length}</b> {isProduct ? 'sản phẩm' : 'mã'}</>
  ) : (
    <b>{isProduct ? 'Tất cả sản phẩm có định mức' : 'Tất cả mã hàng'}</b>
  )
  return (
    <div className="panel">
      <div className="pfilters">
        <div className="field">
          <label>Xem theo</label>
          <div className="chips">
            <span className={isProduct ? 'chip' : 'chip on'}>Mã VTBB</span>
            <span className={isProduct ? 'chip on' : 'chip'}>Mã sản phẩm</span>
          </div>
        </div>
        <div className="field ms">
          <label>{isProduct ? 'Mã sản phẩm — để trống = tất cả sản phẩm có định mức' : 'Mã vật tư — để trống = tất cả mã hàng'}</label>
          <PrintChipsBox codes={codes} emptyText="Tất cả" />
        </div>
      </div>
      <div className="info">{scope}{extras.map((e) => ` · ${e}`).join('')}</div>
    </div>
  )
}

const CHART = { w: 1000, h: 200, l: 52, r: 14, t: 16, b: 30 }

/** "2026-06-30" -> "30/06/26" — nhãn trục ngày của bản mẫu. */
const shortDate = (iso: string): string => { const d = fmtDateStr(iso); return d.length === 10 ? `${d.slice(0, 6)}${d.slice(8)}` : d }

/** Biểu đồ "Diễn biến đơn giá qua các lần mua (VNĐ)": các lần mua CÓ GIÁ của đúng một mã, cũ -> mới. SVG tĩnh, vẽ đúng cỡ khổ giấy. */
export function PrintPriceChart({ series }: { series: readonly PackagingHistoryPoint[] }) {
  if (series.length === 0) return null
  const { w: W, h: H, l, r, t, b } = CHART
  const prices = series.map((p) => p.price)
  const lo = Math.min(...prices)
  const hi = Math.max(...prices)
  const pad = (hi - lo) * 0.15 || hi * 0.05 || 1
  const y0 = Math.max(0, lo - pad)
  const y1 = hi + pad
  const x = (i: number) => (series.length === 1 ? (l + W - r) / 2 : l + (i * (W - l - r)) / (series.length - 1))
  const y = (v: number) => t + (H - t - b) * (1 - (v - y0) / (y1 - y0))
  const last = series.length - 1
  const path = series.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(p.price).toFixed(1)}`).join(' ')
  const step = Math.max(1, Math.ceil(series.length / 10))
  //  Nhãn ngày thưa theo độ rộng thật: không để hai nhãn (nhất là nhãn cuối) đè lên nhau.
  const tickLabels = series.map((p) => shortDate(p.date))
  const tickIndexes = pickDateTickIndexes(series.map((_, i) => x(i)), tickLabels, step)
  const money = (v: number) => Math.round(v).toLocaleString('vi-VN')
  return (
    <div className="panel chart">
      <h4>Diễn biến đơn giá qua các lần mua (VNĐ)</h4>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Diễn biến đơn giá">
        {[y0, (y0 + y1) / 2, y1].map((v) => (
          <g key={v}>
            <line x1={l} x2={W - r} y1={y(v)} y2={y(v)} stroke="#EEF1F5" />
            <text x={l - 8} y={y(v) + 4} textAnchor="end" fontSize="11" fill="#8C939C">{money(v)}</text>
          </g>
        ))}
        <path d={path} fill="none" stroke="#0B6A3A" strokeWidth="2.2" />
        {series.map((p, i) => (
          <circle key={i} cx={x(i)} cy={y(p.price)} r={i === last ? 5 : 3.5} fill={i === last ? '#00AEEF' : '#fff'}
            stroke={i === last ? '#00AEEF' : '#0B6A3A'} strokeWidth="2" />
        ))}
        <text x={Math.min(x(last), W - r - 4)} y={y(series[last].price) - 10} textAnchor="end" fontSize="12" fontWeight="700" fill="#0F3B6E">
          {money(series[last].price)}
        </text>
        {tickIndexes.map((i) => (
          <text key={`t${i}`} x={x(i)} y={H - 8} fontSize="11" fill="#5A5A5A" textAnchor={dateTickAnchor(i, series.length)}>
            {tickLabels[i]}
          </text>
        ))}
      </svg>
    </div>
  )
}

function DiffCell({ row }: { row: PackagingHistoryRow }) {
  const d = diffText(row.diff)
  if (!d) return <PrintDash />
  if (row.diff === 0) return <span className="faint">0</span>
  const p = pctText(row.pct)
  return <span className={(row.diff ?? 0) > 0 ? 'up' : 'down'}>{d}{p && ` (${p})`}</span>
}

/**
 * Bảng "Toàn bộ lịch sử mua hàng" — cùng cột, cùng thứ tự với màn hình. Chế độ sản phẩm (bản mẫu `renderHistBySP`): Mã SP · Tên
 * sản phẩm · Thành phần · Mã VTBB · Tên vật tư · Lần · Ngày mua...; chế độ mã: Lần · Ngày mua · Mã VTBB... `total` là số dòng theo
 * máy chủ (lớn hơn số dòng nếu bản in bị cắt).
 */
export function PrintHistoryTable({ rows, productMode, singleCode, total }: {
  rows: readonly PackagingHistoryRow[]
  productMode: boolean
  singleCode: boolean
  total: number
}) {
  return (
    <div className="panel gap">
      <div className="tbar">
        <span className="ttl">Toàn bộ lịch sử mua hàng</span>
        <span className="cnt">{total.toLocaleString('vi-VN')} {productMode ? 'dòng' : 'lần mua'}</span>
        <span className="cnt">· Giá VNĐ, chưa VAT, bản chụp lúc mua: xanh = đắt hơn lần trước, đỏ = rẻ hơn · Lần 1 = lần mua gần nhất của mã</span>
      </div>
      {rows.length === 0 ? <p className="empty">Không có lần mua nào khớp bộ lọc.</p> : (
        <table>
          <thead>
            <tr>
              {productMode && <><th>Mã SP</th><th>Tên sản phẩm</th><th>Thành phần</th><th>Mã VTBB</th><th>Tên vật tư</th></>}
              <th className="c">Lần</th><th>Ngày mua</th>
              {!productMode && <th>Mã VTBB</th>}
              {!productMode && !singleCode && <th>Tên vật tư</th>}
              <th>Nhà cung cấp</th><th>Kho</th><th className="n">Số lượng</th><th className="n">Đơn giá</th><th className="n">Giá trị mua</th>
              <th className="n">So lần trước</th><th>Nguồn</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const qty = qtyText(r.qty)
              const openPo = r.is_open
              const materialName = r.name || <span className="faint">(chưa có tên)</span>
              return (
                <tr key={historyRowKey(r)} className={r.price === 0 ? 'zero' : undefined}>
                  {productMode && (
                    <>
                      <td className="code"><b>{r.fg_code}</b></td>
                      <td className="name">{r.fg_name || <span className="faint">(chưa có tên)</span>}</td>
                      <td>{historyRoleText(r) || <PrintDash />}</td>
                      <td className="code">{r.code}</td>
                      <td className="name">{materialName}</td>
                    </>
                  )}
                  <td className="c"><b>{r.seq}</b></td>
                  <td>{r.date ? fmtDateStr(r.date) : <PrintDash />}</td>
                  {!productMode && <td className="code">{r.code}</td>}
                  {!productMode && !singleCode && <td className="name">{materialName}</td>}
                  <td>{r.supplier || <PrintDash />}</td>
                  <td className="wh">{r.warehouse || <PrintDash />}</td>
                  <td className="n">{qty ? `${qty}${r.unit ? ` ${r.unit}` : ''}` : <PrintDash />}</td>
                  <td className="n">{r.price === 0 ? '0' : <b>{priceText(r.price) || <PrintDash />}</b>}</td>
                  <td className="n">{amountText(r.amount) || <PrintDash />}</td>
                  <td className="n"><DiffCell row={r} /></td>
                  <td>{openPo && <span className="pbadge">ĐMH đang mở</span>}{r.doc_id > 0 && (r.po_code || `#${r.doc_id}`)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}
