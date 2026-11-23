import type { PackagingImpactProduct, PackagingPart, PackagingSelectedCode } from '../../api/packaging-cost-types'
import { diffText, joinWarnings, pctText, priceText, roleLabel, selectedCodeNote } from '../../utils/packaging-price'
import { PrintDash } from './PackagingPrintShell'
import { PrintChipsBox } from './PackagingPrintWidgets'

/**
 * duoc-CR-784 — các khối của bản in Tác động giá bao bì (bản v1), dựng theo bản mẫu HTML: khối ô lọc (ô mã chọn nhiều + dòng
 * thông tin) liền bảng MÃ ĐÃ CHỌN (đầu navy, ô giá giả định nền vàng), rồi khối SẢN PHẨM BỊ ẢNH HƯỞNG (ô thành phần ghi mã +
 * giá, mã đang chọn tô xanh nhạt). Cùng cột + định dạng với màn hình. Bảng mã đã chọn không có cột "Sàn – Trần": ngưỡng đang
 * tắt (`PACKAGING_LIMITS_ENABLED`). Chênh lệch TĂNG xanh, GIẢM đỏ (luật màu của hệ).
 */

type Num = number | null | undefined
const tone = (v: Num): string | undefined => (typeof v !== 'number' || !Number.isFinite(v) || Math.abs(v) < 1e-6 ? undefined : v > 0 ? 'up' : 'down')
const Price = ({ value }: { value: Num }) => <>{priceText(value) || <PrintDash />}</>
const Diff = ({ value }: { value: Num }) => { const t = diffText(value); return t ? <span className={tone(value)}>{t}</span> : <PrintDash /> }
const Pct = ({ value }: { value: Num }) => { const t = pctText(value); return t ? <span className={tone(value)}>{t}</span> : <PrintDash /> }

/** Năm cột thành phần của định mức: vai trò (`PackagingRole`) + `perCarton` = giá tính cho cả thùng. */
const PART_COLUMNS = [
  { role: 1, perCarton: false }, { role: 2, perCarton: false }, { role: 3, perCarton: false },
  { role: 4, perCarton: true }, { role: 5, perCarton: true },
] as const

/** Khối ô lọc + dòng điều kiện đang bật + bảng MÃ ĐÃ CHỌN (ba thẻ số liệu đã bỏ theo người chủ, 23/11/2026). `extras` = giá giả định / khoảng ngày / từ khóa. */
export function PrintImpactSelection({ codes, extras, rows }: {
  codes: readonly string[]
  extras: readonly string[]
  rows: readonly PackagingSelectedCode[]
}) {
  return (
    <div className="panel">
      <div className="pfilters">
        <div className="field ms">
          <label>Mã chai / nắp / nhãn / nhãn thùng / thùng</label>
          <PrintChipsBox codes={codes} emptyText="Chưa chọn mã" />
        </div>
      </div>
      {extras.length > 0 && <div className="info">{extras.join(' · ')}</div>}
      {rows.length === 0 ? <p className="empty">Các mã đã chọn chưa có trong định mức nào.</p> : (
        <table>
          <thead>
            <tr>
              <th>Mã</th><th>Tên vật tư</th><th>Nhóm</th><th className="n">Giá cũ</th><th className="n">Giá mới</th><th className="n">Giá giả định</th>
              <th className="n">Chênh lệch</th><th className="n">%</th><th className="n">Số SP bị ảnh hưởng</th><th className="n">Min</th><th className="n">Max</th><th>Ghi chú</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.code}>
                <td className="code"><b>{r.code}</b></td>
                <td className="name">{r.name}</td>
                <td>{r.group}</td>
                <td className="n"><Price value={r.old} /></td>
                <td className="n"><Price value={r.new} /></td>
                <td className="n">{r.assumed != null ? <span className="cell-inp"><Price value={r.assumed} /></span> : <span className="cell-inp faint">Bỏ trống</span>}</td>
                <td className="n"><Diff value={r.diff} /></td>
                <td className="n"><Pct value={r.pct} /></td>
                <td className="n">{r.usage}</td>
                <td className="n"><Price value={r.min} /></td>
                <td className="n"><Price value={r.max} /></td>
                <td className="nt"><span className="note">{selectedCodeNote(r, r.applied)}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

/** Ô thành phần: mã trên, giá dưới ("cũ → mới" khi đổi); mã đang chọn tô xanh nhạt cả ô. */
function PartCell({ part }: { part: PackagingPart | undefined }) {
  if (!part?.code) return <td className="pc"><PrintDash /></td>
  const current = part.applied ?? part.new
  const changed = part.old != null && current != null && Math.abs(current - part.old) > 1e-9
  return (
    <td className={part.selected ? 'pc hl' : 'pc'}>
      <div>{part.code}</div>
      <small className={part.selected ? undefined : 'faint'}>
        {current == null ? 'chưa có giá' : changed ? (
          <>{priceText(part.old)} → <b className={tone(current - (part.old ?? 0))}>{priceText(current)}</b></>
        ) : priceText(current)}
      </small>
    </td>
  )
}

/** Khối "Sản phẩm sử dụng các mã đã chọn". `empty` = câu hiện khi không có sản phẩm nào. */
export function PrintImpactProducts({ rows, matched, empty }: { rows: readonly PackagingImpactProduct[]; matched: number; empty: string }) {
  return (
    <div className="panel gap">
      <div className="tbar">
        <span className="ttl">Sản phẩm sử dụng các mã đã chọn</span>
        <span className="cnt">{matched.toLocaleString('vi-VN')} sản phẩm</span>
      </div>
      {rows.length === 0 ? <p className="empty">{empty}</p> : (
        <table>
          <thead>
            <tr>
              <th className="c">STT</th><th>Mã HH</th><th>Tên hàng hóa</th><th className="n">Quy cách thùng</th>
              {PART_COLUMNS.map((p) => <th key={p.role}>{p.perCarton ? `${roleLabel(p.role)} (giá /thùng)` : roleLabel(p.role)}</th>)}
              <th className="n">CP bao bì/chai cũ</th><th className="n">CP bao bì/chai mới</th>
              <th className="n">Tăng/giảm /chai</th><th className="n">Tăng/giảm /thùng</th><th>Ghi chú</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={r.hh_code}>
                <td className="c faint">{i + 1}</td>
                <td className="code">{r.hh_code}</td>
                <td className="name">{r.hh_name}</td>
                <td className="n">{r.carton_qty ? r.carton_qty.toLocaleString('vi-VN') : <PrintDash />}</td>
                {PART_COLUMNS.map((p) => <PartCell key={p.role} part={r.parts.find((x) => x.role === p.role)} />)}
                <td className="n"><Price value={r.cost_old_bottle} /></td>
                <td className="n"><b><Price value={r.cost_applied_bottle} /></b></td>
                <td className="n"><Diff value={r.diff_bottle} /></td>
                <td className="n"><Diff value={r.diff_carton} /></td>
                <td className="nt"><span className="note">{joinWarnings(r.warnings)}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
