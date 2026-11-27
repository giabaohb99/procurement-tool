import type { ReactNode } from 'react'
import NumberInput from '../NumberInput'
import type { PackagingImpactProduct, PackagingSelectedCode } from '../../api/packaging-cost-types'
import { PRICE_DECIMALS } from '../../utils/money'
import { diffColor, joinWarnings, priceText, roleLabel } from '../../utils/packaging-price'
import { CodeLink, DiffText, PctText, PriceText, TrendText } from './PackagingCells'

/**
 * duoc-CR-784 — NỘI DUNG THẺ điện thoại của hai bảng Tác động giá (Mã đã chọn, Sản phẩm bị ảnh hưởng) và của Tổng hợp theo
 * sản phẩm. Thẻ sản phẩm: "lưới 2×2 gọn" (người chủ chốt 26/11/2026); thẻ mã đã chọn: "dải giá + ô gõ rộng" (chốt 27/11/2026). Truyền vào `TableCards.renderCard`: khung thẻ, thanh xếp, ô rỗng
 * vẫn của `TableCards`. Nhãn, màu tăng xanh giảm đỏ, luật ô giá giả định y hệt bảng (và y hệt thẻ `frontend-v2`).
 */

/** Ô số của lưới 2×2: nhãn nhỏ mờ trên, giá trị đậm dưới; vùng giá trị luôn cao tối thiểu bằng ô nhập để bốn ô cao bằng nhau. */
function Tile({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="pkg-tile">
      <span className="tcard-k">{label}</span>
      <div className="pkg-tile-v">{children}</div>
    </div>
  )
}

/** Giá "cũ → mới": đổi giá thì số cũ mờ + mũi tên + số mới đậm tô theo chiều; chưa có giá thì nói thẳng. */
function PriceChange({ from, to }: { from: number | null | undefined; to: number | null | undefined }) {
  if (to == null) return <span className="pkg-muted">chưa có giá</span>
  const changed = from != null && Math.abs(to - from) > 1e-9
  if (!changed) return <span className="pkg-num">{priceText(to)}</span>
  return (
    <span className="pkg-num">
      <span className="pkg-muted">{priceText(from)} →</span>{' '}
      <b style={{ color: diffColor(to - (from ?? 0)) }}>{priceText(to)}</b>
    </span>
  )
}

/**
 * Thẻ của một MÃ ĐÃ CHỌN: mã · nhóm + nút bỏ, tên, MỘT dải giá đọc theo mạch Giá cũ → Giá mới với Chênh lệch căn phải, ô Giá giả
 * định riêng một hàng rộng hết thẻ (dễ gõ bằng ngón tay), chân "n SP · Min–Max".
 */
export function SelectedCodeCard({ row, assumed, onAssumedChange, onRemove }: {
  row: PackagingSelectedCode
  /** Giá đang gõ (chưa qua trễ). */
  assumed: number | undefined
  /** `null` = bỏ giả định, quay về giá bảng giá. */
  onAssumedChange: (code: string, price: number | null) => void
  onRemove: (code: string) => void
}) {
  const warnings = joinWarnings(row.warnings)
  return (
    <>
      <div className="pkg-card-head">
        <div className="pkg-card-code"><CodeLink code={row.code} />{row.group && <span className="pkg-card-grp"> · {row.group}</span>}</div>
        <button className="pkg-x" aria-label={`Bỏ ${row.code}`} title="Bỏ mã này" onClick={() => onRemove(row.code)}><i className="ti ti-x" /></button>
      </div>
      <div className="pkg-card-name" title={row.name}>{row.name || <span className="pkg-muted">(chưa có tên)</span>}</div>
      <div className="pkg-strip">
        <div><span className="tcard-k">Giá cũ</span><div className="pkg-strip-v"><PriceText value={row.old} /></div></div>
        <i className="ti ti-arrow-right pkg-strip-arrow" aria-hidden="true" />
        <div><span className="tcard-k">Giá mới</span><div className="pkg-strip-v"><PriceText value={row.new} /></div></div>
        <div className="pkg-strip-end">
          <span className="tcard-k">Chênh lệch</span>
          <div className="pkg-strip-v"><DiffText value={row.diff} bold /></div>
          <small><PctText value={row.pct} /></small>
        </div>
      </div>
      <div className="pkg-assumed-row">
        <span className="tcard-k">Giá giả định</span>
        {/*  Ô xóa trắng trả 0 — coi là BỎ giả định (giá bao bì 0 đồng không có nghĩa mô phỏng). */}
        <NumberInput className="pkg-assumed" placeholder="Nhập giá" maxDecimals={PRICE_DECIMALS}
          value={assumed ?? 0} onChange={(p) => onAssumedChange(row.code, p > 0 ? p : null)} />
      </div>
      <div className="pkg-card-foot">
        {row.usage.toLocaleString('vi-VN')} SP bị ảnh hưởng · Min–Max {priceText(row.min) || '—'} – {priceText(row.max) || '—'}
      </div>
      {warnings && <div className="pkg-err pkg-card-warn">{warnings}</div>}
    </>
  )
}

/**
 * Thẻ của một SẢN PHẨM (Tác động giá và Tổng hợp theo sản phẩm): mã (+ xu hướng ở Tổng hợp), tên mờ, bốn ô chi phí, rồi các thành
 * phần thành lưới ba cột vai trò | mã | cũ → mới. Thành phần chưa khai mã thì ẩn dòng; thành phần tính theo thùng kèm "/thùng";
 * mã đang chọn tô nền vàng. `overview` = mã bấm được sang Lịch sử + "% chênh" dưới tăng/giảm /chai.
 */
export function ProductCard({ row, overview = false }: { row: PackagingImpactProduct; overview?: boolean }) {
  const newCost = overview ? row.cost_new_bottle : row.cost_applied_bottle
  const warnings = joinWarnings(row.warnings)
  const parts = [1, 2, 3, 4, 5].flatMap((role) => {
    const part = row.parts.find((x) => x.role === role)
    return part?.code ? [{ role, part }] : []
  })
  return (
    <>
      <div className="pkg-card-head">
        <div className="pkg-card-code">{overview ? <CodeLink code={row.fg_code} product /> : <b className="pkg-num">{row.fg_code}</b>}</div>
        {overview && <span className="pkg-card-badge"><TrendText trend={row.trend} /></span>}
      </div>
      <div className="pkg-card-name muted" title={row.fg_name}>{row.fg_name}</div>
      <div className="pkg-tiles">
        <Tile label="CP cũ /chai"><PriceText value={row.cost_old_bottle} /></Tile>
        <Tile label="CP mới /chai"><PriceText value={newCost} /></Tile>
        <Tile label="Tăng/giảm /chai">
          <span className="pkg-tile-diff col"><DiffText value={row.diff_bottle} bold />{overview && <small><PctText value={row.pct} /></small>}</span>
        </Tile>
        <Tile label="Tăng/giảm /thùng"><DiffText value={row.diff_carton} bold /></Tile>
      </div>
      {(parts.length > 0 || row.carton_qty > 0) && (
        <>
          <div className="pkg-card-sec"><span>Thành phần</span>{row.carton_qty > 0 && <span>Quy cách {row.carton_qty.toLocaleString('vi-VN')}</span>}</div>
          <ul className="pkg-card-parts">
            {parts.map(({ role, part }) => {
              const current = part.applied ?? part.new
              return (
                <li key={role} className={part.selected ? 'sel' : undefined}>
                  <span className="pkg-muted">{roleLabel(role)}</span>
                  <span className="pkg-card-pcode">{overview ? <CodeLink code={part.code} /> : part.code}</span>
                  <span className="pkg-card-pprice">
                    <PriceChange from={part.old} to={current} />
                    {(role === 4 || role === 5) && current != null && <span className="pkg-muted"> /thùng</span>}
                  </span>
                </li>
              )
            })}
          </ul>
        </>
      )}
      {warnings && <div className="pkg-card-warn amber">{warnings}</div>}
    </>
  )
}
